#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from my_robot_interfaces.srv import SetLed
from functools import partial

class Battery(Node):
    def __init__(self):
        super().__init__("battery")#nome do nó

        self.battery_state_ = 1
        self.last_time_battery_state_changed_ = self.get_time()
        self.battery_timer_ = self.create_timer(0.1, self.check_battery_state)

    def get_time(self):
        secs, nsecs = self.get_clock().now().seconds_nanoseconds()
        return secs+nsecs /1000000000.0


    def check_battery_state(self):
        time_now = self.get_time()
        if self.battery_state_ == 1:
            if time_now - self.last_time_battery_state_changed_ > 4.0:
                self.battery_state_ = 0
                self.get_logger().info("acabou a bateria, carregando")
                self.last_time_battery_state_changed_ = time_now
                self.call_set_led_server(3, 1)
        else:
            if(time_now - self.last_time_battery_state_changed_ > 6.0):
                self.battery_state_ = 1
                self.get_logger().info("bateria cheia")
                self.last_time_battery_state_changed_ = time_now
                self.call_set_led_server(3, 0)

    def call_set_led_server(self, led_number, state):
        client = self.create_client(SetLed, "set_led")
        while not client.wait_for_service(1.0):
            self.get_logger().info("Esperando servidor")
        
        request = SetLed.Request()
        request.state = state
        request.led_number = led_number

        future = client.call_async(request)
        future.add_done_callback(partial(self.callback_call_set_led, led_number=led_number, state=state))
    
    def callback_call_set_led(self, future, led_number, state):
        try:
            response = future.result()
            self.get_logger().info(str(response.success))
        except Exception as e:
            self.get_logger().info("Falhou %r" % (e,))


def main(args = None):
    rclpy.init(args=args)
    node = Battery()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
