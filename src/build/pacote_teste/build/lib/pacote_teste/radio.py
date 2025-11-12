#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from example_interfaces.msg import String

class radio_robos(Node):
    def __init__(self):
        super().__init__("radio_news")#nome do nó
        self.declare_parameter("name", "R2D2")

        self.nome_ = self.get_parameter("name").value
        self.publisher_ = self.create_publisher(String, "noticias_topic", 10)
        self.timer_ = self.create_timer(1.0, self.callback_noticias_topic)
        self.get_logger().info("postando noticias")
    
    def callback_noticias_topic(self):
        msg = String()
        msg.data = "Oi eu sou o %s" % self.nome_
        self.publisher_.publish(msg)

def main(args = None):
    rclpy.init(args=args)
    node = radio_robos()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
