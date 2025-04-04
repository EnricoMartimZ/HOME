import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch.substitutions import LaunchConfiguration
from ament_index_python import get_package_share_directory
from launch_ros.actions import Node
from launch.conditions import UnlessCondition, IfCondition

def generate_launch_description():
    use_slam_arg = DeclareLaunchArgument(
        "use_slam",
        default_value="true"
    )
    
    use_slam = LaunchConfiguration("use_slam")


    world_arg = DeclareLaunchArgument(
        "world_name",
        default_value="empty",
        description="Nome do mundo a ser carregado pelo Gazebo"
    )

    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("bumperbot_description"),
            "launch",
            "gazebo.launch.py"
        ),
        launch_arguments={"world_name": LaunchConfiguration("world_name")}.items(),
    )

    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("bumperbot_controller"),
            "launch",
            "controller.launch.py"
        ),
        launch_arguments={
            "use_simple_controller": "False",
            "use_python": "True"
        }.items(),
    )

    delayed_controller = TimerAction(
        period=15.0,  # Atraso de 15 segundos
        actions=[controller]
    )
    
    twist_converter = Node(
        package="bumperbot_py",
        executable="twist_converter"
    )

    localization = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("bumperbot_localization"),
            "launch",
            "global_localization.launch.py"
        ),
        condition=UnlessCondition(use_slam)
    )

    slam = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("bumperbot_mapping"),
            "launch",
            "slam.launch.py"
        ),
        condition=IfCondition(use_slam)
    )

    safety_stop = Node(
        package="bumperbot_utils",
        executable="parada_segura",
        output="screen"
    )


    return LaunchDescription([
        use_slam_arg,
        world_arg,
        gazebo,
        delayed_controller,  # Agora o controlador será iniciado após 15 segundos
        twist_converter,
        #safety_stop,
        slam,
        localization,
    ])
