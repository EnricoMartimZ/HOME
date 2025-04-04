from setuptools import find_packages, setup

package_name = 'bumperbot_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='emzx',
    maintainer_email='emzx@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',    
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'simple_parameter = bumperbot_py.simple_parameter:main',
            'simple_turtlesim_kinematics = bumperbot_py.turtlesim_kinematics:main',
            'twist_converter = bumperbot_py.twist_converter:main',
            'simple_tf_kinematics = bumperbot_py.simple_tf_kinematics:main',
            'simple_action_server = bumperbot_py.simple_action_server:main',
            'simple_action_client = bumperbot_py.simple_action_client:main',
            'simple_lifecycle_node = bumperbot_py.simple_lifecycle_node:main',
            'simple_qos_publisher = bumperbot_py.simple_qos_publisher:main',
            'simple_qos_subscriber = bumperbot_py.simple_qos_subscriber:main',
            'keyboard_controller = bumperbot_py.keyboard_controller:main',


        ],
    },
)
