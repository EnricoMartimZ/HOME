import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/emzx/ros2_ws/install/turtlesim_catch_them_all'
