# vision_pipeline_openvino/vision_pipeline_node.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from vision_msgs.msg import Detection2DArray, Detection2D, BoundingBox2D
from geometry_msgs.msg import Pose2D
from cv_bridge import CvBridge
import cv2
import numpy as np

from .openvino_manager import OpenVinoManager
from .face_database import FaceDatabase

class VisionPipelineNode(Node):
    def __init__(self):
        super().__init__('vision_pipeline_node')
        
        # Parâmetros
        self.declare_parameter('models_path', '~/openvino_models')
        self.declare_parameter('device', 'GPU')
        self.declare_parameter('face_confidence', 0.7)
        self.declare_parameter('object_confidence', 0.5)
        
        # Inicialização
        self.bridge = CvBridge()
        self.openvino_manager = OpenVinoManager(device=self.get_parameter('device').value)
        self.face_db = FaceDatabase()
        
        # Caregar modelos
        self.load_models()
        
        # Subscribers
        self.image_subscription = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',
            self.image_callback,
            10
        )
        
        # Publishers
        self.detection_publisher = self.create_publisher(
            Detection2DArray,
            '/vision/detections',
            10
        )
        
        self.debug_image_publisher = self.create_publisher(
            Image,
            '/vision/debug_image',
            10
        )
        
        self.get_logger().info('Vision Pipeline Node iniciado!')
        
    def load_models(self):
        """Carrega todos os modelos OpenVINO"""
        models_path = self.get_parameter('models_path').value
        
        try:
            # Carregar modelo de detecção facial
            face_detection_path = f"{models_path}/intel/face-detection-adas-0001/FP32/face-detection-adas-0001.xml"
            self.openvino_manager.load_face_detection_model(face_detection_path)
            
            # Carregar modelo de reconhecimento facial
            face_recognition_path = f"{models_path}/intel/face-reidentification-retail-0095/FP32/face-reidentification-retail-0095.xml"
            self.openvino_manager.load_face_recognition_model(face_recognition_path)
            
            self.get_logger().info('Modelos carregados com sucesso!')
            
        except Exception as e:
            self.get_logger().error(f'Erro ao carregar modelos: {str(e)}')
            
    def image_callback(self, msg):
        """Callback principal para processar imagens"""
        try:
            # Converter mensagem ROS para OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # Detectar faces
            faces = self.openvino_manager.detect_faces(
                cv_image, 
                self.get_parameter('face_confidence').value
            )
            
            # Processar cada face detectada
            detections = Detection2DArray()
            detections.header = msg.header
            
            debug_image = cv_image.copy()
            
            for face in faces:
                # Extrair embedding e identificar pessoa
                if face['face_crop'].size > 0:
                    embedding = self.openvino_manager.get_face_embedding(face['face_crop'])
                    person_id = self.face_db.identify_face(embedding)
                    
                    # Criar mensagem de detecção
                    detection = Detection2D()
                    detection.header = msg.header
                    
                    # Bounding box
                    bbox = BoundingBox2D()
                    x1, y1, x2, y2 = face['bbox']
                    bbox.center.x = float((x1 + x2) / 2)
                    bbox.center.y = float((y1 + y2) / 2)
                    bbox.size_x = float(x2 - x1)
                    bbox.size_y = float(y2 - y1)
                    detection.bbox = bbox
                    
                    # Informações adicionais
                    detection.results[0].id = person_id if person_id else "unknown"
                    detection.results[0].score = face['confidence']
                    
                    detections.detections.append(detection)
                    
                    # Desenhar no debug image
                    label = f"{person_id if person_id else 'Unknown'}: {face['confidence']:.2f}"
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(debug_image, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Publicar resultados
            self.detection_publisher.publish(detections)
            
            # Publicar debug image
            debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
            self.debug_image_publisher.publish(debug_msg)
            
        except Exception as e:
            self.get_logger().error(f'Erro no processamento: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = VisionPipelineNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()