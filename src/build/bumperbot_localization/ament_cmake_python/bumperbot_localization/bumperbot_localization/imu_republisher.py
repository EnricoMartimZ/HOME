#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import time
from sensor_msgs.msg import Imu

imu_pub = None

def imuCallback(imu):
    global imu_pub
    
    # Mudando o frame_id
    imu.header.frame_id = "base_footprint_ekf"
    
    # Invertendo o sentido de rotação
    # Invertendo o sinal da componente z do quaternion e mantendo o sinal de w
    # Isso efetivamente inverte o ângulo de yaw
    imu.orientation.z = -imu.orientation.z
    
    # Invertendo a velocidade angular no eixo z
    imu.angular_velocity.z = -imu.angular_velocity.z
    
    # Publicando a mensagem com os valores invertidos
    imu_pub.publish(imu)

def main():
    global imu_pub
    rclpy.init()
    node = Node("imu_republisher_node")
    time.sleep(1)

    imu_pub = node.create_publisher(Imu, "imu_ekf", 10)
    imu_sub = node.create_subscription(Imu, "imu/out", imuCallback, 10)

    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()