import cv2
import torch
from ultralytics import YOLO
from ultralytics.engine.results import Results, Masks
import time
import numpy as np


model = YOLO('yolov8n-seg.pt')  

def get_mask_center_point(mask):
    """
    Encontra um ponto central que está dentro da máscara
    """
    # Converter mask para numpy se necessário
    if isinstance(mask, torch.Tensor):
        mask_np = mask.cpu().numpy().astype(np.uint8)
    else:
        mask_np = mask.astype(np.uint8)
    
    # Método 1: Centro de massa (centroid)
    moments = cv2.moments(mask_np)
    if moments["m00"] != 0:
        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])
        
        # Verificar se o centroid está dentro da máscara
        if mask_np[cy, cx] > 0:
            return (cx, cy), "centroid"
    
    
    
    # Método 3: Distance Transform (mais robusto)
    dist_transform = cv2.distanceTransform(mask_np, cv2.DIST_L2, 5)
    _, _, _, max_loc = cv2.minMaxLoc(dist_transform)
    if max_loc:
        return max_loc, "distance_transform"
    
    return None, "failed"

# Inicializar câmera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Pressione 'q' para sair")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    start_time = time.time()
    
    # Detectar e segmentar
    rawFrame = frame.copy()
    results = model(frame, conf=0.5, verbose=False)
    
    # Desenhar resultados
    annotated_frame = results[0].plot()
    
    # Processar máscaras se existirem
    if results[0].masks is not None:
        masks = results[0].masks
        boxes = results[0].boxes
        
        # Para cada máscara detectada
        for i, mask in enumerate(masks.data):
            center_point, method = get_mask_center_point(mask)
            class_name = None
            
            if boxes is not None and i < len(boxes):
                class_id = int(boxes[i].cls)
                class_name = model.names[class_id]
            
            # Só desenhar se for pessoa
            if center_point and class_name == "person":
                cx, cy = center_point
                cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)
                cv2.circle(frame, (cx, cy), 8, (0, 0, 255), 2)
                cv2.putText(frame, f"({cx},{cy})", 
                        (cx + 10, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, f"{class_name} - {method}", 
                        (cx + 10, cy + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                print(f"Objeto {i}: {class_name} - Centro: ({cx}, {cy}) - Método: {method}")

    
    processing_time = time.time() - start_time
    cv2.putText(frame, f"FPS: {1/processing_time:.1f}", 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.imshow('YOLO Segmentation with Center Points', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

