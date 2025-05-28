# #!/usr/bin/env python3

# import rclpy
# from rclpy.node import Node
# from nav_msgs.msg import Odometry
# from sensor_msgs.msg import Imu

# class KalmanFilter(Node):
#     def __init__(self):
#         super().__init__("kalman_filter")#nome do nó
        
#         self.odom_sub_ = self.create_subscription(Odometry, "bumperbot_controller/odom_noisy", self.odomCallback, 10)#encoder
#         self.imu_sub_ = self.create_subscription(Imu, "imu/out", self.imuCallback, 10)#imu
#         self.odom_pub_ = self.create_publisher(Odometry, "bumperbot_controller/odom_kalman", 10)

#         self.mean_ = 0.0
#         self.variance_ = 1000.0

#         self.imu_angular_z_ = 0.0 #qual vamos filtrar --> guarda a ultima recebida do imu
#         self.is_first_odom_ = True
#         self.last_angular_z_ = 0.0

#         self.motion_ = 0.0
#         self.kalman_odom_ = Odometry()

#         self.motion_variance_ = 4.0 #variancia da gaussiana da locomoçao do robo
#         self.measurement_variance_ = 0.5 #variancia da gaussiana do sensor inercial(imu)

#     def measurementUpdate(self):
#         self.mean_ = (self.measurement_variance_* self.mean_ + self.variance_ * self.imu_angular_z_)/(self.variance_ + self.measurement_variance_)
#         self.variance_ = (self.variance_*self.measurement_variance_)/(self.variance_ + self.measurement_variance_)

#     def statePrediction(self):
#         self.mean_ = self.mean_ + self.motion_
#         self.variance_ = self.variance_ + self.motion_variance_

#     def imuCallback(self, imu):
#         self.imu_angular_z_ =  imu.angular_velocity.z
    
#     def odomCallback(self, odom):
#         self.kalman_odom_ = odom

#         if self.is_first_odom_:
#             self.mean_ = odom.twist.twist.angular.z
#             self.last_angular_z_ = odom.twist.twist.angular.z
#             self.is_first_odom_ = False
#             return
        
#         self.motion_ = odom.twist.twist.angular.z - self.last_angular_z_

#         self.statePrediction()
#         self.measurementUpdate()

#         self.kalman_odom_.twist.twist.angular.z = self.mean_
#         self.odom_pub_.publish(self.kalman_odom_)

# def main(args = None):
#     rclpy.init(args=args)
#     node = KalmanFilter()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from geometry_msgs.msg import TransformStamped
from tf_transformations import quaternion_from_euler, euler_from_quaternion
from tf2_ros import TransformBroadcaster
import numpy as np
import math

class ExtendedKalmanFilter(Node):
    def __init__(self):
        super().__init__("extended_kalman_filter")
        
        # Subscribers
        self.odom_encoder_sub_ = self.create_subscription(
            Odometry, "bumperbot_controller/odom_noisy", self.odomEncoderCallback, 10)
        self.imu_sub_ = self.create_subscription(
            Imu, "imu/out", self.imuCallback, 10)
        self.odom_lidar_sub_ = self.create_subscription(
            Odometry, "bumperbot_controller/odom_lidar", self.odomLidarCallback, 10)
        
        # Publishers
        self.odom_pub_ = self.create_publisher(
            Odometry, "bumperbot_controller/odom_kalman", 10)
        
        # TF Broadcaster
        self.br_ = TransformBroadcaster(self)
        self.transform_stamped_ = TransformStamped()
        self.transform_stamped_.header.frame_id = "odom"
        self.transform_stamped_.child_frame_id = "base_footprint_ekf"
        
        # Estado do filtro [x, y, theta, vx, vy, omega]
        self.state_ = np.zeros((6, 1))  # [x, y, theta, vx, vy, omega]
        
        # Matriz de covariância do estado
        self.P_ = np.eye(6) * 1000.0
        
        # Matriz de transição de estado (será atualizada a cada iteração)
        self.F_ = np.eye(6)
        
        # Matriz de covariância do processo
        self.Q_ = np.diag([0.1, 0.1, 0.1, 0.5, 0.5, 0.5])
        
        # Matrizes de observação para cada sensor
        # Encoder: observa [x, y, theta, vx, vy, omega]
        self.H_encoder_ = np.eye(6)
        self.R_encoder_ = np.diag([0.5, 0.5, 0.3, 0.2, 0.2, 0.4])
        
        # IMU: observa apenas omega (velocidade angular)
        self.H_imu_ = np.zeros((1, 6))
        self.H_imu_[0, 5] = 1.0  # omega
        self.R_imu_ = np.array([[0.1]])
        
        # LIDAR: observa [x, y, theta]
        self.H_lidar_ = np.zeros((3, 6))
        self.H_lidar_[0, 0] = 1.0  # x
        self.H_lidar_[1, 1] = 1.0  # y
        self.H_lidar_[2, 2] = 1.0  # theta
        self.R_lidar_ = np.diag([0.2, 0.2, 0.15])
        
        # Dados dos sensores
        self.last_encoder_data_ = None
        self.last_imu_data_ = None
        self.last_lidar_data_ = None
        
        # Controle de tempo
        self.last_time_ = self.get_clock().now()
        self.is_initialized_ = False
        
        # Odometria de saída
        self.kalman_odom_ = Odometry()
        self.kalman_odom_.header.frame_id = "odom"
        self.kalman_odom_.child_frame_id = "base_footprint_ekf"
        
        self.get_logger().info("Extended Kalman Filter initialized")

    def initializeState(self, odom_msg):
        """Inicializa o estado com a primeira leitura do encoder"""
        _, _, yaw = euler_from_quaternion([
            odom_msg.pose.pose.orientation.x,
            odom_msg.pose.pose.orientation.y,
            odom_msg.pose.pose.orientation.z,
            odom_msg.pose.pose.orientation.w
        ])
        
        self.state_[0, 0] = odom_msg.pose.pose.position.x
        self.state_[1, 0] = odom_msg.pose.pose.position.y
        self.state_[2, 0] = yaw
        self.state_[3, 0] = odom_msg.twist.twist.linear.x
        self.state_[4, 0] = odom_msg.twist.twist.linear.y
        self.state_[5, 0] = odom_msg.twist.twist.angular.z
        
        self.is_initialized_ = True
        self.get_logger().info("State initialized")

    def predict(self, dt):
        """Etapa de predição do filtro de Kalman"""
        if dt <= 0:
            return
            
        # Atualiza matriz de transição com base no modelo cinemático
        self.F_ = np.eye(6)
        self.F_[0, 3] = dt  # x = x + vx*dt
        self.F_[1, 4] = dt  # y = y + vy*dt
        self.F_[2, 5] = dt  # theta = theta + omega*dt
        
        # Predição do estado
        self.state_ = np.dot(self.F_, self.state_)
        
        # Normaliza ângulo
        self.state_[2, 0] = self.normalizeAngle(self.state_[2, 0])
        
        # Predição da covariância
        self.P_ = np.dot(np.dot(self.F_, self.P_), self.F_.T) + self.Q_

    def updateEncoder(self, odom_msg):
        """Atualização com dados do encoder"""
        _, _, yaw = euler_from_quaternion([
            odom_msg.pose.pose.orientation.x,
            odom_msg.pose.pose.orientation.y,
            odom_msg.pose.pose.orientation.z,
            odom_msg.pose.pose.orientation.w
        ])
        
        # Medição
        z = np.array([[
            odom_msg.pose.pose.position.x,
            odom_msg.pose.pose.position.y,
            yaw,
            odom_msg.twist.twist.linear.x,
            odom_msg.twist.twist.linear.y,
            odom_msg.twist.twist.angular.z
        ]]).T
        
        self.kalmanUpdate(z, self.H_encoder_, self.R_encoder_)

    def updateIMU(self, imu_msg):
        """Atualização com dados do IMU"""
        z = np.array([[imu_msg.angular_velocity.z]])
        self.kalmanUpdate(z, self.H_imu_, self.R_imu_)

    def updateLidar(self, odom_msg):
        """Atualização com dados do LIDAR"""
        _, _, yaw = euler_from_quaternion([
            odom_msg.pose.pose.orientation.x,
            odom_msg.pose.pose.orientation.y,
            odom_msg.pose.pose.orientation.z,
            odom_msg.pose.pose.orientation.w
        ])
        
        z = np.array([[
            odom_msg.pose.pose.position.x,
            odom_msg.pose.pose.position.y,
            yaw
        ]]).T
        
        self.kalmanUpdate(z, self.H_lidar_, self.R_lidar_)

    def kalmanUpdate(self, z, H, R):
        """Etapa de atualização genérica do filtro de Kalman"""
        # Inovação
        y = z - np.dot(H, self.state_)
        
        # Normaliza ângulos na inovação se necessário
        if H.shape[0] == 3 and H[2, 2] == 1.0:  # Atualização do LIDAR
            y[2, 0] = self.normalizeAngle(y[2, 0])
        elif H.shape[0] == 6:  # Atualização do encoder
            y[2, 0] = self.normalizeAngle(y[2, 0])
        
        # Matriz de covariância da inovação
        S = np.dot(np.dot(H, self.P_), H.T) + R
        
        # Ganho de Kalman
        K = np.dot(np.dot(self.P_, H.T), np.linalg.inv(S))
        
        # Atualização do estado
        self.state_ = self.state_ + np.dot(K, y)
        
        # Normaliza ângulo do estado
        self.state_[2, 0] = self.normalizeAngle(self.state_[2, 0])
        
        # Atualização da covariância
        I_KH = np.eye(6) - np.dot(K, H)
        self.P_ = np.dot(I_KH, self.P_)

    def normalizeAngle(self, angle):
        """Normaliza ângulo para [-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def publishState(self):
        """Publica o estado filtrado como odometria"""
        current_time = self.get_clock().now()
        
        # Converte quaternion
        q = quaternion_from_euler(0, 0, self.state_[2, 0])
        
        # Atualiza mensagem de odometria
        self.kalman_odom_.header.stamp = current_time.to_msg()
        self.kalman_odom_.pose.pose.position.x = self.state_[0, 0]
        self.kalman_odom_.pose.pose.position.y = self.state_[1, 0]
        self.kalman_odom_.pose.pose.position.z = 0.0
        self.kalman_odom_.pose.pose.orientation.x = q[0]
        self.kalman_odom_.pose.pose.orientation.y = q[1]
        self.kalman_odom_.pose.pose.orientation.z = q[2]
        self.kalman_odom_.pose.pose.orientation.w = q[3]
        
        self.kalman_odom_.twist.twist.linear.x = self.state_[3, 0]
        self.kalman_odom_.twist.twist.linear.y = self.state_[4, 0]
        self.kalman_odom_.twist.twist.angular.z = self.state_[5, 0]
        
        # Define covariâncias
        pose_cov = np.zeros(36)
        twist_cov = np.zeros(36)
        
        # Covariância da pose (6x6 -> 36 elementos)
        for i in range(6):
            for j in range(6):
                pose_cov[i*6 + j] = self.P_[i, j]
                twist_cov[i*6 + j] = self.P_[i, j]
        
        self.kalman_odom_.pose.covariance = pose_cov.tolist()
        self.kalman_odom_.twist.covariance = twist_cov.tolist()
        
        # Publica odometria
        self.odom_pub_.publish(self.kalman_odom_)
        
        # Atualiza e publica transform
        self.transform_stamped_.header.stamp = current_time.to_msg()
        self.transform_stamped_.transform.translation.x = self.state_[0, 0]
        self.transform_stamped_.transform.translation.y = self.state_[1, 0]
        self.transform_stamped_.transform.translation.z = 0.0
        self.transform_stamped_.transform.rotation.x = q[0]
        self.transform_stamped_.transform.rotation.y = q[1]
        self.transform_stamped_.transform.rotation.z = q[2]
        self.transform_stamped_.transform.rotation.w = q[3]
        
        self.br_.sendTransform(self.transform_stamped_)

    def odomEncoderCallback(self, msg):
        """Callback para dados do encoder"""
        if not self.is_initialized_:
            self.initializeState(msg)
            self.last_time_ = self.get_clock().now()
            return
        
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time_).nanoseconds / 1e9
        
        if dt > 0:
            self.predict(dt)
            self.updateEncoder(msg)
            self.publishState()
            self.last_time_ = current_time

    def imuCallback(self, msg):
        """Callback para dados do IMU"""
        if not self.is_initialized_:
            return
        
        self.updateIMU(msg)
        self.publishState()

    def odomLidarCallback(self, msg):
        """Callback para dados do LIDAR"""
        if not self.is_initialized_:
            return
        
        self.updateLidar(msg)
        self.publishState()

def main(args=None):
    rclpy.init(args=args)
    node = ExtendedKalmanFilter()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()