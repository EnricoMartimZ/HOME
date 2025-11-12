import cv2
import torch
import numpy as np
import time
import pyrealsense2 as rs
from ultralytics import YOLO

def map_point(point, orig_size, target_size):
    # Maps a 2D point from original size to target size coordinates
    x, y = point
    H1, W1 = orig_size
    H2, W2 = target_size
    return int(x * W2 / W1), int(y * H2 / H1)

def get_mask_center_point(mask):
    """
    Finds a central point inside the mask using centroid or distance transform.
    Returns (point, method) or (None, "failed").
    """
    mask_np = mask.cpu().numpy().astype(np.uint8) if isinstance(mask, torch.Tensor) else mask.astype(np.uint8)

    # Try centroid method
    moments = cv2.moments(mask_np)
    if moments["m00"] != 0:
        cx, cy = int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"])
        if mask_np[cy, cx] > 0:
            return (cx, cy), "centroid"

    # Fallback to distance transform method
    _, _, _, max_loc = cv2.minMaxLoc(cv2.distanceTransform(mask_np, cv2.DIST_L2, 5))
    if max_loc:
        return max_loc, "distance_transform"

    return None, "failed"

def main():
    model = YOLO('yolov8n-seg.pt')

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    pipeline.start(config)

    print("Press 'q' to exit")

    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())
        frame = np.asanyarray(color_frame.get_data())

        start = time.time()
        results = model(frame, conf=0.5, verbose=False)

        # Draw detection results
        annotated_frame = results[0].plot()

        # Process detected masks
        masks = results[0].masks
        boxes = results[0].boxes

        if masks is not None:
            for i, mask in enumerate(masks.data):
                center, method = get_mask_center_point(mask)
                if center and boxes is not None and i < len(boxes):
                    cls_id = int(boxes[i].cls)
                    cls_name = model.names[cls_id]

                    if cls_name == "person":
                        cx, cy = center
                        # Draw circles and text on frame
                        cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)
                        cv2.circle(frame, (cx, cy), 8, (0, 0, 255), 2)
                        depth_val = depth_image[cy, cx]
                        cv2.putText(frame, f"({cx},{cy}) depth {depth_val}",
                                    (cx + 10, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                    (255, 255, 255), 1)
                        cv2.putText(frame, f"{cls_name} - {method}",
                                    (cx + 10, cy + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                                    (255, 255, 255), 1)
                        print(f"Object {i}: {cls_name} - Center: ({cx}, {cy}) - Method: {method}")

        fps = 1 / (time.time() - start)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('YOLO Segmentation with Center Points', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pipeline.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
