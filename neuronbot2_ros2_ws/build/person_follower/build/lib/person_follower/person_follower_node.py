#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
import tf2_ros
from tf2_geometry_msgs import do_transform_pose
import math

class PersonFollowerNode(Node):
    def __init__(self):
        super().__init__('person_follower_node')
        
        # Parâmetros
        self.declare_parameter('yolo_model', 'yolov8n.pt')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('camera_topic', '/camera/color/image_raw')
        self.declare_parameter('depth_topic', '/camera/aligned_depth_to_color/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/color/camera_info')
        self.declare_parameter('target_distance', 1.5)  # distância desejada da pessoa (metros)
        self.declare_parameter('min_detection_interval', 1.0)  # segundos entre atualizações
        
        # Carregar modelo YOLO
        model_path = self.get_parameter('yolo_model').value
        self.get_logger().info(f'Carregando modelo YOLO: {model_path}')
        self.yolo_model = YOLO(model_path)
        
        # Parâmetros internos
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.target_distance = self.get_parameter('target_distance').value
        self.min_detection_interval = self.get_parameter('min_detection_interval').value
        
        # Bridge para conversão de imagens
        self.bridge = CvBridge()
        
        # TF2 para transformações
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Variáveis de estado
        self.camera_info = None
        self.depth_image = None
        self.last_detection_time = self.get_clock().now()
        self.current_goal_handle = None
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image,
            self.get_parameter('camera_topic').value,
            self.image_callback,
            10
        )
        
        self.depth_sub = self.create_subscription(
            Image,
            self.get_parameter('depth_topic').value,
            self.depth_callback,
            10
        )
        
        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            self.get_parameter('camera_info_topic').value,
            self.camera_info_callback,
            10
        )
        
        # Action client para navegação
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        self.get_logger().info('Person Follower Node iniciado!')
        self.get_logger().info('Aguardando servidor de navegação...')
        self.nav_client.wait_for_server()
        self.get_logger().info('Servidor de navegação conectado!')

    def camera_info_callback(self, msg):
        """Armazena informações da câmera"""
        if self.camera_info is None:
            self.camera_info = msg
            self.get_logger().info('Informações da câmera recebidas')

    def depth_callback(self, msg):
        """Armazena imagem de profundidade"""
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        except Exception as e:
            self.get_logger().error(f'Erro ao converter imagem de profundidade: {e}')

    def image_callback(self, msg):
        """Callback principal - detecta pessoa e envia meta de navegação"""
        
        # Verificar intervalo mínimo entre detecções
        current_time = self.get_clock().now()
        time_since_last = (current_time - self.last_detection_time).nanoseconds / 1e9
        
        if time_since_last < self.min_detection_interval:
            return
        
        # Verificar se temos todas as informações necessárias
        if self.camera_info is None or self.depth_image is None:
            return
        
        try:
            # Converter imagem ROS para OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # Detectar pessoas com YOLO
            results = self.yolo_model(cv_image, verbose=False)
            
            # Procurar por pessoas (classe 0 no COCO)
            person_detected = False
            best_person = None
            best_confidence = 0.0
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Classe 0 = pessoa
                    if cls == 0 and conf > self.confidence_threshold:
                        if conf > best_confidence:
                            best_confidence = conf
                            best_person = box
                            person_detected = True
            
            if person_detected and best_person is not None:
                # Calcular posição 3D da pessoa
                goal_pose = self.calculate_person_position(best_person, cv_image)
                
                if goal_pose is not None:
                    # Enviar meta de navegação
                    self.send_navigation_goal(goal_pose)
                    self.last_detection_time = current_time
                    
                    self.get_logger().info(
                        f'Pessoa detectada! Confiança: {best_confidence:.2f} - '
                        f'Navegando para: x={goal_pose.pose.position.x:.2f}, '
                        f'y={goal_pose.pose.position.y:.2f}'
                    )
            
        except Exception as e:
            self.get_logger().error(f'Erro no processamento: {e}')

    def calculate_person_position(self, box, image):
        """Calcula posição 3D da pessoa no frame do mapa"""
        
        # Obter centro da bounding box
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        
        # Obter profundidade no centro da pessoa
        if center_y >= self.depth_image.shape[0] or center_x >= self.depth_image.shape[1]:
            return None
        
        depth = self.depth_image[center_y, center_x]
        
        # Converter para metros (assumindo profundidade em mm)
        if depth == 0 or np.isnan(depth):
            self.get_logger().warn('Profundidade inválida')
            return None
        
        depth_m = depth / 1000.0 if depth > 100 else depth
        
        # Parâmetros intrínsecos da câmera
        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]
        
        # Converter pixel para coordenadas 3D no frame da câmera
        x_cam = (center_x - cx) * depth_m / fx
        y_cam = (center_y - cy) * depth_m / fy
        z_cam = depth_m
        
        # Criar PoseStamped no frame da câmera
        pose_camera = PoseStamped()
        pose_camera.header.frame_id = self.camera_info.header.frame_id
        pose_camera.header.stamp = self.get_clock().now().to_msg()
        
        # Ajustar para manter distância desejada
        # Calcular vetor direção normalizado
        distance_to_person = math.sqrt(x_cam**2 + y_cam**2 + z_cam**2)
        
        if distance_to_person > 0:
            # Posição um pouco mais próxima do robô que a pessoa
            factor = max(0.1, (distance_to_person - self.target_distance) / distance_to_person)
            
            pose_camera.pose.position.x = x_cam * factor
            pose_camera.pose.position.y = y_cam * factor
            pose_camera.pose.position.z = z_cam * factor
        else:
            pose_camera.pose.position.x = x_cam
            pose_camera.pose.position.y = y_cam
            pose_camera.pose.position.z = z_cam
        
        # Orientação apontando para a pessoa
        yaw = math.atan2(y_cam, z_cam)
        pose_camera.pose.orientation.z = math.sin(yaw / 2)
        pose_camera.pose.orientation.w = math.cos(yaw / 2)
        
        try:
            # Transformar para o frame do mapa
            transform = self.tf_buffer.lookup_transform(
                'map',
                pose_camera.header.frame_id,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=1.0)
            )
            
            pose_map = do_transform_pose(pose_camera.pose, transform)
            
            goal_pose = PoseStamped()
            goal_pose.header.frame_id = 'map'
            goal_pose.header.stamp = self.get_clock().now().to_msg()
            goal_pose.pose = pose_map
            
            return goal_pose
            
        except Exception as e:
            self.get_logger().error(f'Erro na transformação TF: {e}')
            return None

    def send_navigation_goal(self, goal_pose):
        """Envia meta de navegação para o Nav2"""
        
        # Cancelar meta anterior se existir
        if self.current_goal_handle is not None:
            try:
                self.current_goal_handle.cancel_goal_async()
            except Exception:
                pass
        
        # Criar nova meta
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = goal_pose
        
        # Enviar meta
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """Callback quando meta é aceita/rejeitada"""
        goal_handle = future.result()
        
        if not goal_handle.accepted:
            self.get_logger().warn('Meta rejeitada pelo navegador')
            self.current_goal_handle = None
            return
        
        self.current_goal_handle = goal_handle
        self.get_logger().info('Meta aceita! Robô navegando...')

def main(args=None):
    rclpy.init(args=args)
    node = PersonFollowerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()