#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

class TwistRelay(Node):
    def __init__(self):
        super().__init__("twist_relay")#nome do nó

        self.controller_sub_ = self.create_subscription(Twist, "/bumperbot_controller/cmd_vel_unstamped", self.controller_twistCallback, 10)
        self.controller_pub_ = self.create_publisher(TwistStamped, "/bumperbot_controller/cmd_vel", 10)

        #com o teclado eu mando direto pro /input_joy/cmd_vel com ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/input_joy/cmd_vel
        '''self.joy_sub_ = self.create_subscription(TwistStamped, "/input_joy/cmd_vel_stamped", self.joy_twistCallback, 10)
        self.joy_pub_ = self.create_publisher(Twist, "/input_joy/cmd_vel", 10)'''

    def controller_twistCallback(self, msg):
        twist_stamped = TwistStamped()
        twist_stamped.header.stamp = self.get_clock().now().to_msg()
        twist_stamped.twist = msg
        self.controller_pub_.publish(twist_stamped)

    def joy_twistCallback(self, msg):
        twist = Twist()
        twist = msg.twist
        self.joy_pub_.publish(twist)

def main(args = None):
    rclpy.init(args=args)
    node = TwistRelay()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
