#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped

class Trajetoria(Node):
    def __init__(self):
        super().__init__("no_trajetoria")#nome do nó
        self.odom_sub_ = self.create_subscription(Odometry, "bumperbot_controller/odom", self.trajetoriaCallback, 10)
        self.path_pub_ = self.create_publisher(Path, "bumperbot_controller/trajectory", 10)
        self.path_ = Path()

    
    def trajetoriaCallback(self, msg):
        self.path_.header.frame_id = msg.header.frame_id
        pose_atual = PoseStamped()
        pose_atual.header.frame_id = msg.header.frame_id
        pose_atual.header.stamp = msg.header.stamp
        pose_atual.pose = msg.pose.pose
        self.path_.poses.append(pose_atual)

        self.path_pub_.publish(self.path_)
         

def main(args = None):
    rclpy.init(args=args)
    node = Trajetoria()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()


'''
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped

class Trajetoria(Node):
    def __init__(self):
        super().__init__("no_trajetoria")#nome do nó
        self.declare_parameter("odom_topic", "bumperbot_controller/odom")

        self.topico_ = self.get_parameter("odom_topic")

        self.odom_sub_ = self.create_subscription(Odometry, str(self.topico_), self.trajetoriaCallback, 10)
        self.path_pub_ = self.create_publisher(Path, "bumperbot_controller/trajectory", 10)
        self.path_ = Path()

    
    def trajetoriaCallback(self, msg):
        self.path_.header.frame_id = msg.header.frame_id
        pose_atual = PoseStamped()
        pose_atual.header.frame_id = msg.header.frame_id
        pose_atual.header.stamp = msg.header.stamp
        pose_atual.pose = msg.pose.pose
        self.path_.poses.append(pose_atual)

        self.path_pub_.publish(self.path_)
         

def main(args = None):
    rclpy.init(args=args)
    node = Trajetoria()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()

'''