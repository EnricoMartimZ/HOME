#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from example_interfaces.msg import Int64

class numbers(Node):
    def __init__(self):
        super().__init__("number_publisher")#nome do nó


        self.declare_parameter("number_to_publish", 0)
        self.declare_parameter("publish_frequency", 1.0) 

        self.numero = self.get_parameter("number_to_publish").value
        self.publish_frequency = self.get_parameter("publish_frequency").value

        self.publisher_ = self.create_publisher(Int64, "number", 10)
        self.timer_ = self.create_timer(1.0/ self.publish_frequency, self.publish_news)
        self.get_logger().info("Primeiro funcionando")

    def publish_news(self):
        msg = Int64()
        msg.data = self.numero
        self.publisher_.publish(msg)
        self.numero += 2
        


def main(args = None):
    rclpy.init(args=args)
    node = numbers()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
