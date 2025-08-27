import cv2
from ultralytics import YOLO


model = YOLO('runs/detect/treinada (falta bandeja)6/weights/best.pt')

# Inicializa a captura de vídeo da câmera padrão (índice 0)
camera = cv2.VideoCapture(0)

# Verifica se a câmera foi aberta corretamente
if not camera.isOpened():
    print("Erro: Não foi possível acessar a câmera.")
    exit()

# Loop para capturar e exibir os frames
while True:
    # Lê um frame da câmera
    status, frame = camera.read()

    # Verifica se o frame foi capturado com sucesso
    if not status:
        print("Erro: Não foi possível capturar o frame.")
        break
    
    r = model(frame, verbose=False)[0]    
    
    if r.boxes is not None:
        frame = r.plot()


    print(r)
    print(type(r))

    # Exibe o frame em uma janela chamada "Câmera"
    cv2.imshow("Camera", frame)

    # Aguarda 1 milissegundo e verifica se a tecla 'q' foi pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera a câmera e fecha todas as janelas
camera.release()
cv2.destroyAllWindows()
