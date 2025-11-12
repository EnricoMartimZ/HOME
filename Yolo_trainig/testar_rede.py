# Importa as bibliotecas necessárias:
# cv2 (OpenCV) para manipulação de vídeo e imagem.
# YOLO da biblioteca ultralytics para usar o modelo de detecção.
import cv2
from ultralytics import YOLO

# Carrega o seu modelo YOLO customizado a partir do arquivo de pesos.
# Este caminho aponta para o resultado de um treinamento que você realizou.
model = YOLO('runs/detect/yoloDatasetCriadoNoPelo6/weights/best.pt')

# Inicializa a captura de vídeo da câmera padrão (geralmente a webcam, índice 0).
camera = cv2.VideoCapture(0)

# Verifica se a conexão com a câmera foi estabelecida com sucesso.
if not camera.isOpened():
    print("Erro: Não foi possível acessar a câmera.")
    exit()

# Loop infinito para processar os frames da câmera continuamente.
while True:
    # Lê um único frame da câmera.
    # 'status' será True se a leitura for bem-sucedida, e 'frame' é a imagem capturada.
    status, frame = camera.read()

    # Se não for possível ler o frame, encerra o loop.
    if not status:
        print("Erro: Não foi possível capturar o frame.")
        break
    
    # Envia o frame para o modelo YOLO para realizar a detecção.
    # 'verbose=False' evita que o modelo imprima muitos logs no console.
    # O resultado '[0]' pega a detecção da primeira (e única) imagem.
    results = model(frame, verbose=False)[0]    
    
    # O método 'plot()' desenha as caixas delimitadoras, rótulos e máscaras
    # diretamente na imagem do frame.
    frame_com_deteccoes = results.plot()

    # Exibe o frame (agora com as detecções) em uma janela chamada "Camera".
    cv2.imshow("Camera", frame_com_deteccoes)

    # Aguarda por uma tecla ser pressionada por 1 milissegundo.
    # Se a tecla for 'q', o loop é interrompido.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Ao sair do loop, libera os recursos da câmera.
camera.release()
# Fecha todas as janelas abertas pelo OpenCV.
cv2.destroyAllWindows()

