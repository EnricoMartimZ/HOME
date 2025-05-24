#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import serial
import math
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3

class EstadoMotores(Node):

    def __init__(self):
        super().__init__("estado_motores")
        self.imu_pub = self.create_publisher(Imu,"imu", 10)
        self.joint_pub = self.create_publisher(JointState,"estado_motores", 10)
        """

        self.declare_parameter("baud_rate", 115200)
        self.declare_parameter("porta_esp", '/dev/ttyACM0')

        self.baud_rate = self.get_parameter("baud_rate").get_parameter_value().integer_value
        self.porta_esp = self.get_parameter("porta_esp").get_parameter_value().string_value

        self.get_logger().info("Using wheel radius %d" % self.baud_rate)
        self.get_logger().info("Using wheel separation %s" % self.porta_esp)"""
        
        self.ser = serial.Serial('/dev/ttyUSB0', 115200)
        self.timer = self.create_timer(0.01, self.ler_serial)#100vezes/seg
            
    def ler_serial(self):
        if self.ser.in_waiting > 0:  # Check if there is data in the buffer
            line = self.ser.readline().decode('utf-8').rstrip()  # Read and decode the data
            self.publicar(line)


# Open the virtual serial port for reading
 # Replace with the correct virtual port

    # rm 24.9 54.8 [24.9 rotacoes] 1 rot = 2pi rad
    def publicar(self, linha_lida:str):
        array = linha_lida.split(" ")
        if(len(array)==5):
            #ee ed ax ay vrz
            self.pos_mot_e = float(array[0])
            self.pos_mot_d = float(array[1])
            self.pos_rad_mot_e = self.pos_mot_e * 2 * math.pi
            self.pos_rad_mot_d = self.pos_mot_d * 2 * math.pi
            msg_motores = JointState()
            time = self.get_clock().now().to_msg()
            msg_motores.header.stamp=time
            msg_motores.position = [self.pos_rad_mot_d ,self.pos_rad_mot_e]
            self.joint_pub.publish(msg_motores)

            self.accel_x =float(array[2])
            self.accel_y =float(array[3])
            self.rot_z =float(array[4])
            imu_msg = Imu()
            imu_msg.linear_acceleration = Vector3(x=float(array[2]),y=float(array[3]),z=0.0)
            imu_msg.angular_velocity = Vector3(x=0.0,y=0.0,z=float(array[4]))
            time = self.get_clock().now().to_msg()
            imu_msg.header.stamp=time
            self.imu_pub.publish(imu_msg)
            self.get_logger().info("\n"+str(imu_msg.linear_acceleration)+"\n"+str(imu_msg.angular_velocity))
            

def main():
    rclpy.init()

    estado_motores = EstadoMotores()
    rclpy.spin(estado_motores)
    
    estado_motores.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()