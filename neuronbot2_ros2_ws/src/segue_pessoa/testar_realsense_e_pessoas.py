#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import message_filters
import cv2
import torch
import numpy as np
import time
from ultralytics import YOLO
import math
from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
import tf2_geometry_msgs
from rclpy.duration import Duration


def quaternion_from_euler(roll, pitch, yaw):
    """
    Convert euler angles to quaternion
    """
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    q = [0] * 4
    q[0] = cy * cp * cr + sy * sp * sr  # w
    q[1] = cy * cp * sr - sy * sp * cr  # x
    q[2] = sy * cp * sr + cy * sp * cr  # y
    q[3] = sy * cp * cr - cy * sp * sr  # z

    return q


def map_point(point, orig_size, target_size):
    x, y = point
    H1, W1 = orig_size
    H2, W2 = target_size
    return int(x * W2 / W1), int(y * H2 / H1)


def get_mask_center_point(mask):
    """
    Finds a central point inside the mask using centroid or distance transform.
    Returns (point, method) or (None, "failed").
    """
    mask_np = mask.cpu().numpy().astype(np.uint8) if isinstance(mask, torch.Tensor) else mask.astype(np.uint8)

    # Try centroid method
    moments = cv2.moments(mask_np)
    if moments["m00"] != 0:
        cx, cy = int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"])
        if mask_np[cy, cx] > 0:
            return (cx, cy), "centroid"

    # Fallback to distance transform method
    _, _, _, max_loc = cv2.minMaxLoc(cv2.distanceTransform(mask_np, cv2.DIST_L2, 5))
    if max_loc:
        return max_loc, "distance_transform"

    return None, "failed"


class YoloDepthNav2Node(Node):
    def __init__(self):
        super().__init__('yolo_depth_nav2_node')
        
        # Declare parameters with smaller default values
        self.declare_parameter('stop_distance', 0.5)
        self.declare_parameter('goal_offset', 0.2)
        self.declare_parameter('tf_buffer_cache_time', 30.0)  # Increased buffer cache time
        
        self.stop_distance = self.get_parameter('stop_distance').value
        self.goal_offset = self.get_parameter('goal_offset').value
        tf_cache_time = self.get_parameter('tf_buffer_cache_time').value
        
        # Initialize CV Bridge
        self.bridge = CvBridge()
        
        # Load YOLO model
        self.model = YOLO('yolov8n-seg.pt')
        self.get_logger().info("YOLO model loaded")
        
        # Camera intrinsics
        self.fx = None
        self.fy = None
        self.cx = None
        self.cy = None
        self.camera_info_received = False
        
        # TF2 Buffer and Listener with increased cache time
        self.tf_buffer = Buffer(cache_time=Duration(seconds=tf_cache_time))
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Publisher for Nav2 goal
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        
        # Last published goal for visualization
        self.last_goal = None
        
        # Subscribe to camera info
        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            '/camera_depth_frame/camera_info',
            self.camera_info_callback,
            10
        )
        
        # Create subscribers using message_filters for synchronization
        self.color_sub = message_filters.Subscriber(
            self, 
            Image, 
            '/camera_depth_frame/image_raw'
        )
        self.depth_sub = message_filters.Subscriber(
            self, 
            Image, 
            '/camera_depth_frame/depth/image_raw'
        )
        
        # Synchronize the topics
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.color_sub, self.depth_sub], 
            queue_size=10, 
            slop=0.1
        )
        self.ts.registerCallback(self.callback)
        
        self.get_logger().info("Subscribed to color and depth topics")
        self.get_logger().info(f"TF2 buffer cache time: {tf_cache_time}s")
        self.get_logger().info(f"Stop distance: {self.stop_distance}m, Goal offset: {self.goal_offset}m")
        self.get_logger().info(f"Total approach distance: {self.stop_distance + self.goal_offset}m")
        self.get_logger().info("Press 'q' in the image window to exit")

    def camera_info_callback(self, msg):
        """
        Callback to receive camera intrinsic parameters
        """
        if not self.camera_info_received:
            self.fx = msg.k[0]
            self.fy = msg.k[4]
            self.cx = msg.k[2]
            self.cy = msg.k[5]
            self.camera_info_received = True
            self.get_logger().info(
                f"Camera intrinsics received: fx={self.fx:.2f}, fy={self.fy:.2f}, "
                f"cx={self.cx:.2f}, cy={self.cy:.2f}"
            )

    def pixel_to_camera_coords(self, pixel_x, pixel_y, depth):
        """
        Converts pixel coordinates and depth to 3D camera coordinates.
        Returns (x, y, z) in camera frame.
        """
        if not self.camera_info_received or depth <= 0:
            return None, None, None
        
        x_cam = float((pixel_x - self.cx) * depth / self.fx)
        y_cam = float((pixel_y - self.cy) * depth / self.fy)
        z_cam = float(depth)
        
        return x_cam, y_cam, z_cam

    def calculate_goal_in_map(self, person_x_cam, person_y_cam, person_z_cam):
        """
        Calculate the goal position in map frame to stop at a certain distance
        in front of the detected person.
        """
        try:
            # Use Time(0) to get the latest available transform
            # This avoids extrapolation errors
            transform_cam_to_base = self.tf_buffer.lookup_transform(
                'base_link',
                'camera_depth_frame',
                rclpy.time.Time(),  # Get latest available transform
                timeout=Duration(seconds=0.5)
            )
            
            # Create person position in camera frame as PoseStamped
            person_point_cam = PoseStamped()
            person_point_cam.header.frame_id = 'camera_depth_frame'
            person_point_cam.header.stamp = self.get_clock().now().to_msg()
            person_point_cam.pose.position.x = float(person_z_cam)
            person_point_cam.pose.position.y = float(-person_x_cam)
            person_point_cam.pose.position.z = 0.0
            person_point_cam.pose.orientation.w = 1.0
            person_point_cam.pose.orientation.x = 0.0
            person_point_cam.pose.orientation.y = 0.0
            person_point_cam.pose.orientation.z = 0.0
            
            # Transform PoseStamped to base_link
            person_point_base = tf2_geometry_msgs.do_transform_pose_stamped(
                person_point_cam,
                transform_cam_to_base
            )
            
            # Calculate distance and angle to person in base_link frame
            person_distance = math.sqrt(
                person_point_base.pose.position.x**2 + 
                person_point_base.pose.position.y**2
            )
            person_angle = math.atan2(
                person_point_base.pose.position.y, 
                person_point_base.pose.position.x
            )
            
            # Calculate goal distance (stop before reaching person)
            goal_distance = person_distance - self.stop_distance - self.goal_offset
            
            if goal_distance <= 0.1:
                self.get_logger().warn(
                    f"Person too close! Distance: {person_distance:.2f}m "
                    f"< minimum approach distance: {self.stop_distance + self.goal_offset:.2f}m"
                )
                return None
            
            # Calculate goal position in base_link frame
            goal_x_base = float(goal_distance * math.cos(person_angle))
            goal_y_base = float(goal_distance * math.sin(person_angle))
            
            # Create goal pose in base_link frame
            goal_base = PoseStamped()
            goal_base.header.frame_id = 'base_link'
            goal_base.header.stamp = self.get_clock().now().to_msg()
            goal_base.pose.position.x = goal_x_base
            goal_base.pose.position.y = goal_y_base
            goal_base.pose.position.z = 0.0
            
            # Orientation: face the person
            quat = quaternion_from_euler(0, 0, person_angle)
            goal_base.pose.orientation.w = float(quat[0])
            goal_base.pose.orientation.x = float(quat[1])
            goal_base.pose.orientation.y = float(quat[2])
            goal_base.pose.orientation.z = float(quat[3])
            
            # Transform goal from base_link to map frame
            # Use Time(0) for latest available transform
            transform_base_to_map = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                rclpy.time.Time(),  # Get latest available transform
                timeout=Duration(seconds=0.5)
            )
            
            # Transform the entire PoseStamped
            goal_map = tf2_geometry_msgs.do_transform_pose_stamped(
                goal_base,
                transform_base_to_map
            )
            
            # Update header for map frame
            goal_map.header.frame_id = 'map'
            goal_map.header.stamp = self.get_clock().now().to_msg()
            
            return goal_map
            
        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().warn(f"Transform error: {str(e)}")
            return None
        except Exception as e:
            self.get_logger().error(f"Unexpected error: {str(e)}")
            return None

    def draw_goal_on_image(self, frame):
        """
        Draw the last published goal information on the image
        """
        if self.last_goal is None:
            return
        
        # Draw info box
        start_y = frame.shape[0] - 140
        start_x = 10
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (start_x - 5, start_y - 25), 
                     (450, frame.shape[0] - 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Goal information
        cv2.putText(frame, "PUBLISHED GOAL:", 
                    (start_x, start_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        cv2.putText(frame, 
                    f"Position: ({self.last_goal.pose.position.x:.2f}, {self.last_goal.pose.position.y:.2f})", 
                    (start_x, start_y + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.putText(frame, 
                    f"Frame: {self.last_goal.header.frame_id}", 
                    (start_x, start_y + 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.putText(frame, 
                    f"Stop Dist: {self.stop_distance:.2f}m, Offset: {self.goal_offset:.2f}m", 
                    (start_x, start_y + 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)
        
        cv2.putText(frame, 
                    "Status: GOAL SENT", 
                    (start_x, start_y + 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def callback(self, color_msg, depth_msg):
        """
        Callback function that processes synchronized color and depth images
        """
        try:
            # Convert ROS Image messages to OpenCV format
            color_frame = self.bridge.imgmsg_to_cv2(color_msg, desired_encoding='bgr8')
            depth_frame = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding='32FC1')
            
            depth_image = depth_frame.copy()
            
            start = time.time()
            results = self.model(color_frame, conf=0.5, verbose=False)
            
            # Process detected masks
            masks = results[0].masks
            boxes = results[0].boxes
            
            if masks is not None:
                for i, mask in enumerate(masks.data):
                    center, method = get_mask_center_point(mask)
                    if center and boxes is not None and i < len(boxes):
                        cls_id = int(boxes[i].cls)
                        cls_name = self.model.names[cls_id]
                        
                        if cls_name == "person":
                            cx, cy = center
                            
                            # Draw circles and text on frame
                            cv2.circle(color_frame, (cx, cy), 5, (0, 255, 255), -1)
                            cv2.circle(color_frame, (cx, cy), 8, (0, 0, 255), 2)
                            
                            # Get depth value at center point
                            depth_val = depth_image[cy, cx]
                            
                            # Convert to camera 3D coordinates
                            x_cam, y_cam, z_cam = self.pixel_to_camera_coords(cx, cy, depth_val)
                            
                            if x_cam is not None:
                                # Calculate and publish goal
                                goal_pose = self.calculate_goal_in_map(x_cam, y_cam, z_cam)
                                
                                if goal_pose is not None:
                                    self.goal_pub.publish(goal_pose)
                                    self.last_goal = goal_pose
                                    
                                    cv2.putText(
                                        color_frame, 
                                        f"Goal sent! Dist: {z_cam:.2f}m",
                                        (cx + 10, cy - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 
                                        0.5,
                                        (0, 255, 0), 
                                        2
                                    )
                                    
                                    self.get_logger().info(
                                        f"Goal published - Person at {z_cam:.2f}m, "
                                        f"Goal in map: x={goal_pose.pose.position.x:.2f}, "
                                        f"y={goal_pose.pose.position.y:.2f}"
                                    )
                                else:
                                    cv2.putText(
                                        color_frame, 
                                        "Person too close or TF error!",
                                        (cx + 10, cy - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 
                                        0.5,
                                        (0, 165, 255), 
                                        2
                                    )
            
            # Draw goal information on image
            self.draw_goal_on_image(color_frame)
            
            fps = 1 / (time.time() - start)
            cv2.putText(color_frame, f"FPS: {fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('YOLO Nav2 Goal Setter', color_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.get_logger().info("Shutting down...")
                rclpy.shutdown()
                
        except Exception as e:
            self.get_logger().error(f"Error processing images: {str(e)}")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = YoloDepthNav2Node()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
