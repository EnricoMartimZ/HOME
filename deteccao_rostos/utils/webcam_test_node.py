# vision_pipeline_openvino/webcam_test_node.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading

from openvino_manager import OpenVinoManager
from face_database import FaceDatabase

class WebcamTestNode(Node):
    def __init__(self):
        super().__init__('webcam_test_node')
        
        # Inicialização
        self.bridge = CvBridge()
        self.openvino_manager = OpenVinoManager(device='GPU')
        self.face_db = FaceDatabase()
        
        # Caregar modelos
        self.load_models()
        
        # Publishers
        self.debug_image_publisher = self.create_publisher(
            Image,
            '/vision/debug_image',
            10
        )
        
        # Iniciar captura de webcam
        self.cap = cv2.VideoCapture(0)  # Webcam padrão
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Timer para processar frames
        self.timer = self.create_timer(0.033, self.process_frame)  # ~30 FPS
        
        self.get_logger().info('Webcam Test Node iniciado!')
        
    def load_models(self):
        """Carrega modelos OpenVINO"""
        try:
            models_path = "~/openvino_models"
            face_detection_path = f"{models_path}/intel/face-detection-adas-0001/FP32/face-detection-adas-0001.xml"
            face_recognition_path = f"{models_path}/intel/face-reidentification-retail-0095/FP32/face-reidentification-retail-0095.xml"
            
            self.openvino_manager.load_face_detection_model(face_detection_path)
            self.openvino_manager.load_face_recognition_model(face_recognition_path)
            
            self.get_logger().info('Modelos carregados!')
        except Exception as e:
            self.get_logger().error(f'Erro ao carregar modelos: {e}')
            
    def process_frame(self):
        """Processa frame da webcam"""
        ret, frame = self.cap.read()
        if not ret:
            return
            
        try:
            # Medir tempo de inferência
            start_time = cv2.getTickCount()
            
            # Detectar faces
            faces = self.openvino_manager.detect_faces(frame, confidence_threshold=0.5)
            
            # Calcular FPS
            end_time = cv2.getTickCount()
            fps = cv2.getTickFrequency() / (end_time - start_time)
            
            # Desenhar resultados
            debug_image = frame.copy()
            
            for face in faces:
                if face['face_crop'].size > 0:
                    # Tentar identificar
                    embedding = self.openvino_manager.get_face_embedding(face['face_crop'])
                    person_id = self.face_db.identify_face(embedding)
                    
                    # Desenhar bounding box
                    x1, y1, x2, y2 = face['bbox']
                    label = f"{person_id if person_id else 'Unknown'}: {face['confidence']:.2f}"
                    
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(debug_image, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Mostrar FPS
            cv2.putText(debug_image, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # Publicar para ROS
            debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
            self.debug_image_publisher.publish(debug_msg)
            
        except Exception as e:
            self.get_logger().error(f'Erro no processamento: {e}')
            
    def destroy_node(self):
        if hasattr(self, 'cap'):
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = WebcamTestNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()