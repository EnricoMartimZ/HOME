#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from my_robot_interfaces.action import Fibonacci
import time


class SimpleActionClient(Node):
    def __init__(self):
        super().__init__("simple_action_client")

        self.action_client_ = ActionClient(self, Fibonacci, "fibonacci")
        self.action_client_.wait_for_server()
        self.goal = Fibonacci.Goal()
        self.goal.order = 10
        self.future = self.action_client_.send_goal_async(self.goal, feedback_callback=self.feedbackCallback)
        self.future.add_done_callback(self.responseCallback)
    
    #executado quando mandarmos o goal --> fala se o server aceitou ou nao o nosso request
    def responseCallback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info("Goal rejected.")
            return
        self.get_logger().info("Goal accepted.")
        self.future = goal_handle.get_result_async()
        self.future.add_done_callback(self.resultCallback)
    
    #executado quando o server aceitou nosso goal e começou a executar nosso goal --> roda quando acabar apenas
    def resultCallback(self, future):
        result = future.result().result
        self.get_logger().info("Result {0}".format(result.sequence))
        rclpy.shutdown()


    def feedbackCallback(self, feedback_msg):
        self.get_logger().info("Received feedback: {0}".format(feedback_msg.feedback.partial_sequence))


def main(args = None):
    rclpy.init(args=args)
    node = SimpleActionClient()
    rclpy.spin(node)


if __name__ == "__main__":
    main()
