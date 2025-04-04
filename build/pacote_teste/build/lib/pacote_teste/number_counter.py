#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from example_interfaces.msg import Int64
from example_interfaces.srv import SetBool

class number_contagem(Node):
    def __init__(self):
        super().__init__("number_counter")#nome do nó

        self.count = 0
        self.subscriber_ = self.create_subscription(Int64, "number", self.callback_robot_news, 10)
        self.publisher_ = self.create_publisher(Int64, "number_count", 10)
        self.timer_ = self.create_timer(0.5, self.publish_count)
        self.get_logger().info("number_contagem comecou")
        self.server_ = self.create_service(SetBool, "reset_number_count", self.callback_reset_number_count)
    
    def callback_robot_news(self, msg):
        self.get_logger().info((str(self.count) + " - " + str(msg.data)))
        self.count += 1

    def publish_count(self):
        msg = Int64()
        msg.data = self.count
        self.publisher_.publish(msg)

    def callback_reset_number_count(self, request, response):
        if request.data:
            self.count = 0
            response.success = True
            response.message = "Resetou contador"
        else:
            response.success = False
            response.message = "Contador nao resetou"
        return response

def main(args = None):
    rclpy.init(args=args)
    node = number_contagem()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()


'''     self.server_ = self.create_service(SetBool, "add_two_ints", self.callback_add_two_ints)
        self.get_logger().info("Oi") 

    def reset_number_count(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info(str(request.a)+ " + " +str(request.b) + " = " + str(response.sum))
        return response 
'''