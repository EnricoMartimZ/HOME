import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/pc/Documents/GitHub/HOME/src/install/turtlesim_catch_them_all'
