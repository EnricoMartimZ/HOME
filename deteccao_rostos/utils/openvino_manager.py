import numpy as np
import cv2
from openvino.runtime import Core
from typing import List, Tuple, Dict, Any

class OpenVinoManager:
    def __init__(self, device: str = "GPU"):
        self.core = Core()
        self.device = device
        self.face_detection_net = None
        self.face_recognition_net = None
        self.object_detection_net = None
        
    def load_face_detection_model(self, model_path: str):
        """Carrega modelo de detecção facial"""
        model = self.core.read_model(model_path)
        self.face_detection_net = self.core.compile_model(model, self.device)
        
    def load_face_recognition_model(self, model_path: str):
        """Carrega modelo de reconhecimento facial"""
        model = self.core.read_model(model_path)
        self.face_recognition_net = self.core.compile_model(model, self.device)
        
    def load_object_detection_model(self, model_path: str):
        """Carrega modelo de detecção de objetos"""
        model = self.core.read_model(model_path)
        self.object_detection_net = self.core.compile_model(model, self.device)
        
    def detect_faces(self, image: np.ndarray, confidence_threshold: float = 0.5) -> List[Dict]:
        """Detecta faces na imagem"""
        if self.face_detection_net is None:
            return []
            
        # Pré-processamento
        input_layer = next(iter(self.face_detection_net.inputs))
        n, c, h, w = input_layer.shape
        
        resized_image = cv2.resize(image, (w, h))
        input_image = np.expand_dims(resized_image.transpose(2, 0, 1), 0)
        
        # Inferência
        result = self.face_detection_net([input_image])
        output = result[next(iter(self.face_detection_net.outputs))]
        
        # Pós-processamento
        faces = []
        h_orig, w_orig = image.shape[:2]
        
        for detection in output[0][0]:
            confidence = detection[2]
            if confidence > confidence_threshold:
                x1 = int(detection[3] * w_orig)
                y1 = int(detection[4] * h_orig)
                x2 = int(detection[5] * w_orig)
                y2 = int(detection[6] * h_orig)
                
                faces.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float(confidence),
                    'face_crop': image[y1:y2, x1:x2]
                })
                
        return faces
        
    def get_face_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """Extrai embedding da face"""
        if self.face_recognition_net is None:
            return np.array([])
            
        # Pré-processamento
        input_layer = next(iter(self.face_recognition_net.inputs))
        n, c, h, w = input_layer.shape
        
        resized_face = cv2.resize(face_crop, (w, h))
        input_face = np.expand_dims(resized_face.transpose(2, 0, 1), 0)
        
        # Inferência
        result = self.face_recognition_net([input_face])
        embedding = result[next(iter(self.face_recognition_net.outputs))]
        
        return embedding[0]
        
    def detect_objects(self, image: np.ndarray, confidence_threshold: float = 0.5) -> List[Dict]:
        """Detecta objetos na imagem"""
        if self.object_detection_net is None:
            return []
            
        # Implementação similar à detecção de faces
        # Adaptar conforme o modelo YOLO escolhido
        objects = []
        return objects