import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math

class JazzyLidarAngleFilter(Node):
    def __init__(self):
        super().__init__('jazzy_lidar_angle_filter')
        
        # Declare parâmetros para permitir ajustes em tempo de execução
        self.declare_parameter('angle_min', 0.0)  # -45 graus
        self.declare_parameter('angle_max', math.pi)   # +45 graus
        
        # Obter valores dos parâmetros
        self.angle_min = self.get_parameter('angle_min').value
        self.angle_max = self.get_parameter('angle_max').value
        
        # Criar subscription e publisher
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',  # Ajuste para o tópico correto do Jazzy
            self.scan_callback,
            10)
        self.publisher = self.create_publisher(
            LaserScan,
            '/filtered_scan',
            10)
    
    def scan_callback(self, msg):
        # Criar uma cópia da mensagem para modificar
        filtered_scan = LaserScan()
        filtered_scan.header = msg.header
        filtered_scan.angle_min = self.angle_min
        filtered_scan.angle_max = self.angle_max
        
        # Calcular o índice inicial e final com base nos ângulos desejados
        angle_increment = msg.angle_increment
        start_idx = int((self.angle_min - msg.angle_min) / angle_increment)
        end_idx = int((self.angle_max - msg.angle_min) / angle_increment)
        
        # Garantir que os índices estejam dentro dos limites
        start_idx = max(0, start_idx)
        end_idx = min(len(msg.ranges) - 1, end_idx)
        
        # Definir o novo incremento angular e contar
        filtered_scan.angle_increment = angle_increment
        filtered_scan.time_increment = msg.time_increment
        filtered_scan.scan_time = msg.scan_time
        filtered_scan.range_min = msg.range_min
        filtered_scan.range_max = msg.range_max
        
        # Filtrar os dados de alcance e intensidade (se disponíveis)
        filtered_scan.ranges = msg.ranges[start_idx:end_idx+1]
        if len(msg.intensities) > 0:
            filtered_scan.intensities = msg.intensities[start_idx:end_idx+1]
        
        # Publicar o scan filtrado
        self.publisher.publish(filtered_scan)

def main(args=None):
    rclpy.init(args=args)
    node = JazzyLidarAngleFilter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()