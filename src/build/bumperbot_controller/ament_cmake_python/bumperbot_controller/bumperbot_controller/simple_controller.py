#!/usr/bin/env python3
from sensor_msgs.msg import JointState
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import TwistStamped, TransformStamped
import numpy as np
from rclpy.time import Time
from rclpy.constants import S_TO_NS
import math
from nav_msgs.msg import Odometry
from tf_transformations import quaternion_from_euler
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster
import serial

class SimpleController(Node):
    def __init__(self):
        super().__init__("simple_controller")

        # Parameters
        self.declare_parameter("wheel_radius", 0.033)
        self.declare_parameter("wheel_separation", 0.17)

        self.wheel_radius_ = self.get_parameter("wheel_radius").get_parameter_value().double_value
        self.wheel_separation_ = self.get_parameter("wheel_separation").get_parameter_value().double_value

        # Validate parameters
        if self.wheel_radius_ <= 0 or self.wheel_separation_ <= 0:
            self.get_logger().error("Invalid wheel parameters!")
            raise ValueError("Wheel radius and separation must be positive")

        # State variables
        self.left_wheel_prev_pos_ = 0.0
        self.right_wheel_prev_pos_ = 0.0
        self.prev_time_ = self.get_clock().now()
        self.x_ = 0.0
        self.y_ = 0.0
        self.theta_ = 0.0

        # Speed conversion matrix
        self.speed_conversion_ = np.array([
            [self.wheel_radius_/2, self.wheel_radius_/2],
            [self.wheel_radius_/self.wheel_separation_, -self.wheel_radius_/self.wheel_separation_]
        ])

        # Publishers and Subscribers
        self.wheel_cmd_pub_ = self.create_publisher(Float64MultiArray, "simple_velocity_controller/commands", 10)
        self.vel_sub_ = self.create_subscription(TwistStamped, "bumperbot_controller/cmd_vel", self.velCallback, 10)
        self.joint_sub_ = self.create_subscription(JointState, "joint_states", self.jointCallback, 10)
        self.odom_pub_ = self.create_publisher(Odometry, "bumperbot_controller/odom", 10)
        self.wheel_sub_ = self.create_subscription(Float64MultiArray, "simple_velocity_controller/commands", self.wheel_motorCallback, 10)

        # Odometry message setup
        self.odom_msg_ = Odometry()
        self.odom_msg_.header.frame_id = "odom"
        self.odom_msg_.child_frame_id = "base_footprint"
        self.odom_msg_.pose.pose.orientation.x = 0.0
        self.odom_msg_.pose.pose.orientation.y = 0.0
        self.odom_msg_.pose.pose.orientation.z = 0.0
        self.odom_msg_.pose.pose.orientation.w = 1.0
        
        # Odometry covariance matrices
        self.odom_msg_.pose.covariance = [
            0.1, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.1, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.1, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.1, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.1, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.1
        ]
        self.odom_msg_.twist.covariance = self.odom_msg_.pose.covariance

        # TF Broadcaster setup
        self.br_ = TransformBroadcaster(self)
        self.transform_stamped_ = TransformStamped()
        self.transform_stamped_.header.frame_id = "odom"
        self.transform_stamped_.child_frame_id = "base_footprint"
        self.transform_stamped_.header.stamp = self.get_clock().now().to_msg()

        # Static TF Broadcaster for fixed transforms
        self.static_br_ = StaticTransformBroadcaster(self)

        # Serial connection setup
        try:
            self.serial = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
            self.serial.flush()
            self.get_logger().info("Serial connection established")
        except serial.SerialException as e:
            self.get_logger().error(f"Could not open serial port: {e}")
            self.serial = None

        self.get_logger().info("Simple Controller node started")

    def velCallback(self, msg):
        robot_speed = np.array([[msg.twist.linear.x],
                               [msg.twist.angular.z]])
        wheel_speed = np.matmul(np.linalg.inv(self.speed_conversion_), robot_speed)
        wheel_speed_msg = Float64MultiArray()
        wheel_speed_msg.data = [wheel_speed[1, 0], wheel_speed[0, 0]]
        self.wheel_cmd_pub_.publish(wheel_speed_msg)

    def jointCallback(self, msg):
        current_time = self.get_clock().now()
        dt = (current_time - self.prev_time_).nanoseconds / S_TO_NS
        if dt <= 0:
            dt = 1e-9  # small epsilon to avoid division by zero

        dp_left = msg.position[1] - self.left_wheel_prev_pos_
        dp_right = msg.position[0] - self.right_wheel_prev_pos_
        
        self.left_wheel_prev_pos_ = msg.position[1]
        self.right_wheel_prev_pos_ = msg.position[0]
        self.prev_time_ = current_time

        phi_left = dp_left / dt
        phi_right = dp_right / dt

        linear = (self.wheel_radius_ * phi_right + self.wheel_radius_ * phi_left) / 2
        angular = (self.wheel_radius_ * phi_right - self.wheel_radius_ * phi_left) / self.wheel_separation_

        d_s = (self.wheel_radius_ * dp_right + self.wheel_radius_ * dp_left) / 2
        d_theta = (self.wheel_radius_ * dp_right - self.wheel_radius_ * dp_left) / self.wheel_separation_
        
        self.theta_ += d_theta
        self.theta_ = math.fmod(self.theta_, 2 * math.pi)
        self.x_ += d_s * math.cos(self.theta_)
        self.y_ += d_s * math.sin(self.theta_)
        
        q = quaternion_from_euler(0, 0, self.theta_)
        
        # Update odometry message
        now = current_time.to_msg()
        self.odom_msg_.header.stamp = now
        self.odom_msg_.pose.pose.position.x = self.x_
        self.odom_msg_.pose.pose.position.y = self.y_
        self.odom_msg_.pose.pose.orientation.x = q[0]
        self.odom_msg_.pose.pose.orientation.y = q[1]
        self.odom_msg_.pose.pose.orientation.z = q[2]
        self.odom_msg_.pose.pose.orientation.w = q[3]
        self.odom_msg_.twist.twist.linear.x = linear
        self.odom_msg_.twist.twist.angular.z = angular

        # Update transform
        self.transform_stamped_.transform.translation.x = self.x_
        self.transform_stamped_.transform.translation.y = self.y_
        self.transform_stamped_.transform.rotation.x = q[0]
        self.transform_stamped_.transform.rotation.y = q[1]
        self.transform_stamped_.transform.rotation.z = q[2]
        self.transform_stamped_.transform.rotation.w = q[3]
        self.transform_stamped_.header.stamp = now

        # Publish odometry and transform
        self.odom_pub_.publish(self.odom_msg_)
        self.br_.sendTransform(self.transform_stamped_)

    def wheel_motorCallback(self, msg: Float64MultiArray):
        if self.serial is None:
            self.get_logger().warn("No serial connection available")
            return
            
        cmd_vel_esq = msg.data[0]
        cmd_vel_dir = msg.data[1]
        self.get_logger().info(f"Left: {round(cmd_vel_esq)}, Right: {round(cmd_vel_dir)}")
        mensagem = f"Me {round(cmd_vel_esq)} Md {round(cmd_vel_dir)}\n"
        try:
            self.serial.write(mensagem.encode('utf-8'))
        except serial.SerialException as e:
            self.get_logger().error(f"Serial write failed: {e}")

    def destroy_node(self):
        if hasattr(self, 'serial') and self.serial is not None:
            self.serial.close()
            self.get_logger().info("Serial connection closed")
        super().destroy_node()

def main():
    rclpy.init()
    simple_controller = SimpleController()
    try:
        rclpy.spin(simple_controller)
    except KeyboardInterrupt:
        pass
    finally:
        simple_controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()