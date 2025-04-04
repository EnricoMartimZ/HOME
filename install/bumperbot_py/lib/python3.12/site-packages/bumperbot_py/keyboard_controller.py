#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Header
import sys
import termios
import tty
import select
import threading
import time

class KeyboardController(Node):
    def __init__(self):
        # Inicializar nó ROS 2
        super().__init__('keyboard_controller')
        
        # Publicador para enviar comandos de velocidade do tipo TwistStamped
        self.cmd_vel_pub = self.create_publisher(
            TwistStamped, 
            'bumperbot_controller/cmd_vel', 
            10
        )
        
        # Configurações de velocidade
        self.MAX_LINEAR_VEL = 1.0
        self.MAX_ANGULAR_VEL = 1.0
        self.LINEAR_STEP = 0.05
        self.ANGULAR_STEP = 0.1
        
        # Velocidades atuais
        self.linear_vel = 0.0
        self.angular_vel = 0.0
        
        # Estado das teclas
        self.key_pressed = {
            'w': False,
            'a': False,
            's': False,
            'd': False
        }
        
        # Configuração para leitura de teclas
        self.settings = termios.tcgetattr(sys.stdin)
        
        # Timer para atualização contínua
        self.create_timer(0.1, self.update_and_publish)  # 10Hz
    
    def get_key(self):
        """Obter a tecla pressionada sem bloqueio"""
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key
    
    def process_key(self, key):
        """Processar tecla pressionada"""
        if key in ['w', 'a', 's', 'd']:
            self.key_pressed[key] = True
        elif key == ' ':  # Espaço para parar
            self.stop_robot()
            for k in self.key_pressed:
                self.key_pressed[k] = False
        elif key == '\x03':  # Ctrl+C
            self.stop_robot()
            raise KeyboardInterrupt
    
    def process_key_release(self, key):
        """Processar tecla liberada"""
        if key in ['w', 'a', 's', 'd']:
            self.key_pressed[key] = False
    
    def update_velocity(self):
        """Atualizar velocidades com base nas teclas pressionadas"""
        if self.key_pressed['w']:
            self.linear_vel = min(self.linear_vel + self.LINEAR_STEP, self.MAX_LINEAR_VEL)
        elif self.key_pressed['s']:
            self.linear_vel = max(self.linear_vel - self.LINEAR_STEP, -self.MAX_LINEAR_VEL)
        else:
            # Desacelerar gradualmente quando não há comando linear
            if self.linear_vel > 0:
                self.linear_vel = max(0, self.linear_vel - self.LINEAR_STEP/2)
            elif self.linear_vel < 0:
                self.linear_vel = min(0, self.linear_vel + self.LINEAR_STEP/2)
        
        if self.key_pressed['a']:
            self.angular_vel = min(self.angular_vel + self.ANGULAR_STEP, self.MAX_ANGULAR_VEL)
        elif self.key_pressed['d']:
            self.angular_vel = max(self.angular_vel - self.ANGULAR_STEP, -self.MAX_ANGULAR_VEL)
        else:
            # Desacelerar gradualmente quando não há comando angular
            if self.angular_vel > 0:
                self.angular_vel = max(0, self.angular_vel - self.ANGULAR_STEP/2)
            elif self.angular_vel < 0:
                self.angular_vel = min(0, self.angular_vel + self.ANGULAR_STEP/2)
    
    def update_and_publish(self):
        """Método de callback para o timer"""
        self.update_velocity()
        self.send_velocity_command()
    
    def send_velocity_command(self):
        """Enviar comando de velocidade para o robô usando TwistStamped"""
        twist_stamped = TwistStamped()
        
        # Configurar o cabeçalho com timestamp atual
        twist_stamped.header = Header()
        twist_stamped.header.stamp = self.get_clock().now().to_msg()
        twist_stamped.header.frame_id = "base_link"  # Frame de referência
        
        # Configurar velocidades
        twist_stamped.twist.linear.x = self.linear_vel
        twist_stamped.twist.angular.z = self.angular_vel
        
        # Publicar a mensagem
        self.cmd_vel_pub.publish(twist_stamped)
    
    def stop_robot(self):
        """Parar o robô imediatamente"""
        self.linear_vel = 0.0
        self.angular_vel = 0.0
        
        twist_stamped = TwistStamped()
        twist_stamped.header = Header()
        twist_stamped.header.stamp = self.get_clock().now().to_msg()
        twist_stamped.header.frame_id = "base_link"
        
        self.cmd_vel_pub.publish(twist_stamped)
    
    def run(self):
        """Executar o controlador de teclado"""
        print("Controlador de Teclado para ROS 2 Gazebo")
        print("----------------------------------")
        print("Publicando em: bumperbot_controller/cmd_vel (TwistStamped)")
        print("Teclas de controle:")
        print("  W: para frente")
        print("  S: para trás")
        print("  A: girar esquerda")
        print("  D: girar direita")
        print("  Espaço: parar")
        print("  Ctrl+C: sair")
        print("Mantenha as teclas pressionadas para acelerar")
        
        try:
            while rclpy.ok():
                key = self.get_key()
                
                if key in ['w', 'a', 's', 'd', ' ', '\x03']:
                    self.process_key(key)
                elif key == '\x1b':  # Sequência de tecla de escape (tecla liberada)
                    # Processar sequências de escape
                    sys.stdin.read(1)
                    key_release = sys.stdin.read(1)
                    if key_release in ['w', 'a', 's', 'd']:
                        self.process_key_release(key_release)
                
                time.sleep(0.05)  # Pequeno delay para evitar consumo excessivo de CPU
        
        except KeyboardInterrupt:
            pass
        
        finally:
            # Restaurar configurações do terminal
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            print("\nControlador finalizado.")

def main(args=None):
    # Inicializar ROS 2
    rclpy.init(args=args)
    
    # Criar e executar o controlador
    controller = KeyboardController()
    
    # Executar a interface de teclado em uma thread separada
    keyboard_thread = threading.Thread(target=controller.run)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    
    # Executar o loop principal do ROS 2 em outra thread
    try:
        # Executar spin em thread separada para permitir o controle do teclado
        executor_thread = threading.Thread(target=rclpy.spin, args=(controller,))
        executor_thread.daemon = True
        executor_thread.start()
        
        # Aguardar a thread do teclado terminar
        keyboard_thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        # Finalizar o nó e encerrar o ROS 2
        controller.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()