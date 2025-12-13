# vision_pipeline_openvino/face_database.py
import numpy as np
import pickle
import os
from typing import Dict, List, Optional

class FaceDatabase:
    def __init__(self, database_path: str = "face_database.pkl"):
        self.database_path = database_path
        self.known_faces: Dict[str, np.ndarray] = {}
        self.load_database()
        
    def load_database(self):
        """Carrega database de faces conhecidas"""
        if os.path.exists(self.database_path):
            with open(self.database_path, 'rb') as f:
                self.known_faces = pickle.load(f)
                
    def save_database(self):
        """Salva database de faces"""
        with open(self.database_path, 'wb') as f:
            pickle.dump(self.known_faces, f)
            
    def add_face(self, name: str, embedding: np.ndarray):
        """Adiciona nova face ao database"""
        self.known_faces[name] = embedding
        self.save_database()
        
    def identify_face(self, embedding: np.ndarray, threshold: float = 0.8) -> Optional[str]:
        """Identifica face comparando com database"""
        if not self.known_faces:
            return None
            
        min_distance = float('inf')
        identified_person = None
        
        for name, known_embedding in self.known_faces.items():
            distance = np.linalg.norm(embedding - known_embedding)
            if distance < min_distance:
                min_distance = distance
                identified_person = name
                
        if min_distance < threshold:
            return identified_person
        return None
        
    def list_known_faces(self) -> List[str]:
        """Lista todas as pessoas no database"""
        return list(self.known_faces.keys())