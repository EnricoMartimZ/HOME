import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/emzx/neuronbot2_ros2_ws/install/neuronbot2_led'
