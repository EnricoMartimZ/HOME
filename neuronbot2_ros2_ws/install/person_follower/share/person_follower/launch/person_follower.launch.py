from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    
    # Declarar argumentos do launch
    yolo_model_arg = DeclareLaunchArgument(
        'yolo_model',
        default_value='yolov8n.pt',
        description='Caminho para o modelo YOLO (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt)'
    )
    
    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='Limiar de confiança para detecção (0.0 - 1.0)'
    )
    
    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic',
        default_value='/camera/color/image_raw',
        description='Tópico da imagem RGB da câmera'
    )
    
    depth_topic_arg = DeclareLaunchArgument(
        'depth_topic',
        default_value='/camera/aligned_depth_to_color/image_raw',
        description='Tópico da imagem de profundidade'
    )
    
    camera_info_topic_arg = DeclareLaunchArgument(
        'camera_info_topic',
        default_value='/camera/color/camera_info',
        description='Tópico de informações da câmera'
    )
    
    target_distance_arg = DeclareLaunchArgument(
        'target_distance',
        default_value='1.5',
        description='Distância alvo da pessoa em metros'
    )
    
    min_detection_interval_arg = DeclareLaunchArgument(
        'min_detection_interval',
        default_value='1.0',
        description='Intervalo mínimo entre detecções em segundos'
    )
    
    # Nó person_follower
    person_follower_node = Node(
        package='person_follower',
        executable='person_follower_node',
        name='person_follower',
        output='screen',
        parameters=[{
            'yolo_model': LaunchConfiguration('yolo_model'),
            'confidence_threshold': LaunchConfiguration('confidence_threshold'),
            'camera_topic': LaunchConfiguration('camera_topic'),
            'depth_topic': LaunchConfiguration('depth_topic'),
            'camera_info_topic': LaunchConfiguration('camera_info_topic'),
            'target_distance': LaunchConfiguration('target_distance'),
            'min_detection_interval': LaunchConfiguration('min_detection_interval'),
        }]
    )
    
    return LaunchDescription([
        yolo_model_arg,
        confidence_threshold_arg,
        camera_topic_arg,
        depth_topic_arg,
        camera_info_topic_arg,
        target_distance_arg,
        min_detection_interval_arg,
        person_follower_node,
    ])