import pyrealsense2 as rs
import numpy as np
import cv2

def map_point(point, orig_size, target_size):
    x1, y1 = point
    W1, H1 = orig_size
    W2, H2 = target_size

    x2 = x1 * W2 / W1
    y2 = y1 * H2 / H1

    return (int(x2), int(y2))

# Cria um pipeline para capturar os dados da RealSense
pipeline = rs.pipeline()
pipeline.start()

try:
    while True:
        # Pega os frames disponíveis
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        # Converte os frames para arrays numpy
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())


        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        print(depth_colormap.shape)
        print(depth_image.shape)
        cv2.circle(depth_colormap, map_point((200,100),color_image.shape[:2], depth_image.shape), 8, (0, 0, 255), 2)
        cv2.circle(color_image, (200,100), 8, (0, 0, 255), 2)
        # Mostra as imagens capturadas
        cv2.imshow('Color frame', color_image)
        cv2.imshow('Depth frame', depth_colormap)

        # Sai com a tecla 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
