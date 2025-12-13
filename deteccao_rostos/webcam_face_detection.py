import cv2
import numpy as np
from pathlib import Path
from openvino import Core
import time
import torch
from facenet_pytorch import InceptionResnetV1
import pickle
import json
from PIL import Image
import torch.nn.functional as F

class FaceRecognitionWebcam:
    def __init__(self, models_path="~/openvino_models", database_path="face_database.pkl"):
        """Detector com reconhecimento facial otimizado - OpenVINO + InceptionResnetV1"""
        print("🚀 Iniciando detector facial otimizado...")
        
        # OpenVINO setup
        self.core = Core()
        self.device = "GPU" if "GPU" in self.core.available_devices else "CPU"
        print(f"✓ OpenVINO usando {self.device}")
        
        # PyTorch setup
        self.torch_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"✓ PyTorch usando {self.torch_device}")
        
        self.models_path = Path(models_path).expanduser()
        self.database_path = Path(database_path)
        
        # Modelos
        self.face_net = None  # OpenVINO para detecção
        self.resnet = None    # InceptionResnetV1 para embeddings
        
        # Base de dados de faces conhecidas (embeddings já normalizados)
        self.known_faces = {}  # {nome: normalized_embedding}
        self.confidence_threshold = 0.6
        self.similarity_threshold = 0.6  # Para reconhecimento
        self.face_size = 160  # Tamanho padrão para InceptionResnetV1
        
        # Estatísticas
        self.frame_count = 0
        self.start_time = time.time()
        
        # Inicializar modelos
        if not self._load_models():
            raise Exception("Não foi possível carregar os modelos")
            
        # Carregar base de dados
        self._load_face_database()
        
    def _load_models(self):
        """Carrega modelos otimizados: OpenVINO + InceptionResnetV1"""
        try:
            # 1. OpenVINO para detecção rápida
            model_path = (self.models_path / "intel" / "face-detection-adas-0001" / 
                         "FP32" / "face-detection-adas-0001.xml")
            
            if not model_path.exists():
                print(f"❌ Modelo OpenVINO não encontrado: {model_path}")
                print("Execute: omz_downloader --name face-detection-adas-0001")
                return False
                
            model = self.core.read_model(str(model_path))
            self.face_net = self.core.compile_model(model, self.device)
            print("✓ Modelo OpenVINO carregado")
            
            # 2. InceptionResnetV1 para embeddings
            self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.torch_device)
            print("✓ InceptionResnetV1 carregado")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelos: {e}")
            return False
            
    def _load_face_database(self):
        """Carrega base de dados de faces conhecidas"""
        if self.database_path.exists():
            try:
                with open(self.database_path, 'rb') as f:
                    self.known_faces = pickle.load(f)
                print(f"✓ Base carregada: {len(self.known_faces)} pessoas")
                for name in self.known_faces.keys():
                    print(f"   - {name}")
            except Exception as e:
                print(f"⚠️ Erro ao carregar base: {e}")
                self.known_faces = {}
        else:
            print("⚠️ Base de dados não encontrada - modo apenas detecção")
            self.known_faces = {}
            
    def _normalize_embedding(self, embedding):
        """Normaliza embedding usando L2 norm"""
        return embedding / np.linalg.norm(embedding)
        
    def _preprocess_face_for_embedding(self, face_image):
        """Preprocessa face para InceptionResnetV1"""
        # Redimensionar para 160x160 (padrão do modelo)
        face_resized = cv2.resize(face_image, (self.face_size, self.face_size))
        
        # Converter BGR -> RGB
        face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        
        # Normalizar [0,255] -> [-1,1]
        face_normalized = (face_rgb.astype(np.float32) - 127.5) / 128.0
        
        # Converter para tensor PyTorch
        face_tensor = torch.from_numpy(face_normalized.transpose(2, 0, 1)).unsqueeze(0)
        
        return face_tensor.to(self.torch_device)
        
    def _generate_embedding(self, face_image):
        """Gera embedding normalizado a partir da imagem da face"""
        try:
            # Preprocessar
            face_tensor = self._preprocess_face_for_embedding(face_image)
            
            # Gerar embedding
            with torch.no_grad():
                embedding = self.resnet(face_tensor).cpu().numpy().flatten()
            
            # Normalizar L2
            normalized_embedding = self._normalize_embedding(embedding)
            
            return normalized_embedding
            
        except Exception as e:
            print(f"❌ Erro ao gerar embedding: {e}")
            return None
    def save_face_database(self):
        """Salva base de dados"""
        try:
            with open(self.database_path, 'wb') as f:
                pickle.dump(self.known_faces, f)
            print(f"✓ Base salva: {self.database_path}")
        except Exception as e:
            print(f"❌ Erro ao salvar base: {e}")
            
    def add_person_to_database(self, name, face_coords, frame):
        """Adiciona pessoa à base usando bounding box do OpenVINO"""
        try:
            x1, y1, x2, y2, _ = face_coords
            
            # Extrair face com margem
            margin = 20
            face_x1 = max(0, x1 - margin)
            face_y1 = max(0, y1 - margin)
            face_x2 = min(frame.shape[1], x2 + margin)
            face_y2 = min(frame.shape[0], y2 + margin)
            
            face_image = frame[face_y1:face_y2, face_x1:face_x2]
            
            if face_image.size == 0:
                print(f"❌ Face inválida para {name}")
                return False
            
            # Gerar embedding normalizado
            embedding = self._generate_embedding(face_image)
            
            if embedding is not None:
                # Salvar na base
                self.known_faces[name] = embedding
                self.save_face_database()
                print(f"✓ {name} adicionado à base (embedding normalizado)")
                return True
            else:
                print(f"❌ Falha ao gerar embedding para {name}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao adicionar {name}: {e}")
            return False
            
    def detect_faces(self, frame):
        """Detecta faces com OpenVINO (rápido)"""
        # Preparar entrada
        input_layer = next(iter(self.face_net.inputs))
        n, c, h, w = input_layer.shape
        
        resized_frame = cv2.resize(frame, (w, h))
        input_frame = np.expand_dims(resized_frame.transpose(2, 0, 1), 0)
        
        # Inferência
        result = self.face_net([input_frame])
        detections = result[next(iter(self.face_net.outputs))]
        
        # Processar resultados
        faces = []
        h_orig, w_orig = frame.shape[:2]
        
        for detection in detections[0][0]:
            confidence = detection[2]
            if confidence > self.confidence_threshold:
                x1 = int(detection[3] * w_orig)
                y1 = int(detection[4] * h_orig)
                x2 = int(detection[5] * w_orig)
                y2 = int(detection[6] * h_orig)
                
                # Validar coordenadas
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w_orig, x2), min(h_orig, y2)
                
                if x2 > x1 and y2 > y1:
                    faces.append((x1, y1, x2, y2, confidence))
                    
        return faces
        
    def recognize_face(self, frame, face_coords):
        """Reconhece face usando embedding normalizado e similaridade cosseno otimizada"""
        if not self.known_faces:
            return "Desconhecido", 0.0
            
        try:
            x1, y1, x2, y2, _ = face_coords
            
            # Extrair face com margem (mesmo processo do add_person)
            margin = 20
            face_x1 = max(0, x1 - margin)
            face_y1 = max(0, y1 - margin)
            face_x2 = min(frame.shape[1], x2 + margin)
            face_y2 = min(frame.shape[0], y2 + margin)
            
            face_image = frame[face_y1:face_y2, face_x1:face_x2]
            
            if face_image.size == 0:
                return "Erro", 0.0
            
            # Gerar embedding normalizado
            embedding = self._generate_embedding(face_image)
            
            if embedding is not None:
                # Comparar com base (ambos já normalizados - similaridade cosseno = dot product)
                best_match = "Desconhecido"
                best_similarity = 0.0
                
                for name, known_embedding in self.known_faces.items():
                    # Como ambos embeddings estão normalizados, similaridade cosseno = dot product
                    similarity = np.dot(embedding, known_embedding)
                    
                    if similarity > best_similarity and similarity > self.similarity_threshold:
                        best_similarity = similarity
                        best_match = name
                        
                return best_match, best_similarity
            else:
                return "Erro embedding", 0.0
                
        except Exception as e:
            print(f"⚠️ Erro no reconhecimento: {e}")
            return "Erro", 0.0
            
    def draw_faces_with_recognition(self, frame, faces):
        """Desenha faces com nomes reconhecidos"""
        for i, face_coords in enumerate(faces):
            x1, y1, x2, y2, conf = face_coords
            
            # Reconhecer face
            name, similarity = self.recognize_face(frame, face_coords)
            
            # Escolher cor baseada no reconhecimento
            if name != "Desconhecido" and not name.startswith("Erro"):
                color = (0, 255, 0)  # Verde para conhecidos
                label = f"{name} ({similarity:.2f})"
            else:
                color = (0, 255, 255)  # Amarelo para desconhecidos
                label = f"Face {i+1} ({conf:.2f})"
            
            # Desenhar retângulo
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Calcular posição do texto
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            text_x = x1
            text_y = y1 - 10 if y1 - 10 > text_size[1] else y1 + text_size[1] + 10
            
            # Fundo do texto
            cv2.rectangle(frame, (text_x, text_y - text_size[1] - 5), 
                         (text_x + text_size[0], text_y + 5), color, -1)
            
            # Texto
            cv2.putText(frame, label, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                       
        return frame
        
    def draw_info(self, frame, faces):
        """Desenha informações do sistema"""
        # Calcular FPS
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        # Informações
        info = [
            f"FPS: {fps:.1f}",
            f"Faces: {len(faces)}",
            f"Base: {len(self.known_faces)} pessoas",
            f"Device: {self.device}/{self.torch_device}",
            f"Otimizado: OpenVINO+InceptionResnet",
            "",
            "Controles:",
            "ESC - Sair",
            "S - Screenshot", 
            "A - Adicionar pessoa"
        ]
        
        for i, text in enumerate(info):
            if text:  # Pular linhas vazias
                cv2.putText(frame, text, (10, 30 + i * 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                           
        return frame
        
    def capture_and_add_person(self, frame, faces):
        """Captura face atual e adiciona pessoa à base"""
        if not faces:
            print("❌ Nenhuma face detectada para adicionar")
            return
            
        # Usar primeira face detectada
        face_coords = faces[0]
        
        # Pedir nome
        print("\n📝 Adicionando nova pessoa...")
        name = input("Digite o nome da pessoa: ").strip()
        
        if name and self.add_person_to_database(name, face_coords, frame):
            print(f"✅ {name} adicionado com sucesso!")
        else:
            print("❌ Falha ao adicionar pessoa")
            
    def run(self, camera_id=0):
        """Executa reconhecimento facial na webcam"""
        print(f"📹 Abrindo câmera {camera_id}...")
        
        # Abrir câmera
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Erro ao abrir câmera {camera_id}")
            return
            
        # Configurar câmera
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"✓ Câmera configurada: {width}x{height}")
        
        # Criar janela
        window_name = 'Reconhecimento Facial'
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        
        print("🎬 Reconhecimento iniciado!")
        print("   ESC - Sair | S - Screenshot | A - Adicionar pessoa")
        
        try:
            while True:
                # Capturar frame
                success, frame = cap.read()
                if not success:
                    print("❌ Falha ao capturar frame")
                    break
                
                # Detectar faces
                faces = self.detect_faces(frame)
                
                # Desenhar com reconhecimento
                if faces:
                    frame = self.draw_faces_with_recognition(frame, faces)
                    
                frame = self.draw_info(frame, faces)
                
                # Mostrar frame
                cv2.imshow(window_name, frame)
                
                # Processar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    print("🛑 Saindo...")
                    break
                elif key == ord('s'):  # Screenshot
                    filename = f"screenshot_{int(time.time())}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"📸 Screenshot salva: {filename}")
                elif key == ord('a'):  # Adicionar pessoa
                    self.capture_and_add_person(frame, faces)
                    
        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
            
        finally:
            # Limpeza
            print("🧹 Limpando recursos...")
            if cap and cap.isOpened():
                cap.release()
            cv2.destroyWindow(window_name)
            cv2.waitKey(1)
            
        # Estatísticas finais
        total_time = time.time() - self.start_time
        print(f"✅ Sessão finalizada:")
        print(f"   ⏱️  Tempo total: {total_time:.1f}s")
        print(f"   📊 Frames processados: {self.frame_count}")
        print(f"   📈 FPS médio: {self.frame_count/total_time:.1f}")
        print(f"   👥 Pessoas na base: {len(self.known_faces)}")

def main():
    """Função principal"""
    import sys
    
    try:
        # Argumentos opcionais
        models_path = sys.argv[1] if len(sys.argv) > 1 else "~/openvino_models"
        camera_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        database_path = sys.argv[3] if len(sys.argv) > 3 else "face_database.pkl"
        
        print("=" * 60)
        print("🎯 RECONHECIMENTO FACIAL OTIMIZADO")
        print("   OpenVINO (detecção) + InceptionResnetV1 (embedding)")
        print("   Embeddings L2 normalizados + Similaridade cosseno")
        print("=" * 60)
        
        # Criar e executar
        detector = FaceRecognitionWebcam(models_path, database_path)
        detector.run(camera_id)
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        print("\n💡 Dicas:")
        print("   • Instale: pip install facenet-pytorch torch")
        print("   • Execute: omz_downloader --name face-detection-adas-0001")
        print("   • Verifique se PyTorch está instalado")
        print("   • Teste camera_id diferente (0, 1, 2...)")
        print("   • Embeddings são normalizados L2 para melhor precisão")
    
    print("\n👋 Até logo!")

if __name__ == "__main__":
    main()