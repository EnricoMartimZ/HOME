#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

class TwistConverter(Node):
    def __init__(self):
        super().__init__('twist_converter')

        self.subscription = self.create_subscription(Twist, 'cmd_vel', self.twist_callback, 10)
            
        # Create publisher for TwistStamped messages
        self.publisher = self.create_publisher(TwistStamped, 'bumperbot_controller/cmd_vel', 10)

    def twist_callback(self, twist_msg):
        # Create new TwistStamped message
        stamped_msg = TwistStamped()
        
        # Set the timestamp to current time
        stamped_msg.header.stamp = self.get_clock().now().to_msg()
        stamped_msg.header.frame_id = "base_link"
        
        # Copy the twist data
        stamped_msg.twist = twist_msg
        
        # Publish the converted message
        self.publisher.publish(stamped_msg)

def main():
    rclpy.init()
    converter = TwistConverter()
    rclpy.spin(converter)
    converter.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()