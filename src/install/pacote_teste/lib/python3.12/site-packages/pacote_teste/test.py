#!/usr/bin/env python3
import rclpy
from rclpy.node import Node


def main(args = None):
    rclpy.init(args = None)
    node = Node("py_teste")
    node.get_logger().info("Rola")
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
