#!/usr/bin/env python3
"""Launch the 6-wheel UGV (lidar + depth camera) into square_world."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_share = get_package_share_directory('ugv_robot')
    xacro_path = os.path.join(pkg_share, 'urdf', 'ugv_robot.urdf.xacro')
    world_path = os.path.join(pkg_share, 'worlds', 'square_world.sdf')
    bridge_yaml = os.path.join(pkg_share, 'config', 'ugv_bridge.yaml')

    robot_description = xacro.process_file(xacro_path).toxml()

    use_sim_time = LaunchConfiguration('use_sim_time')
    use_teleop = LaunchConfiguration('use_teleop')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use simulation clock')

    declare_use_teleop = DeclareLaunchArgument(
        'use_teleop', default_value='true',
        description='Launch teleop_twist_keyboard in its own terminal window')

    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', world_path, '-r'],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time,
        }]
    )

    spawn_robot = TimerAction(
        period=5.0,
        actions=[Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-topic', '/robot_description',
                '-name', 'ugv_robot',
                '-z', '0.2',
            ],
            output='screen'
        )]
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        parameters=[{'config_file': bridge_yaml, 'use_sim_time': use_sim_time}],
        output='screen'
    )

    teleop = TimerAction(
        period=7.0,
        actions=[ExecuteProcess(
            cmd=['xterm', '-hold', '-e', 'ros2', 'run', 'teleop_twist_keyboard',
                 'teleop_twist_keyboard', '--ros-args', '-r', 'cmd_vel:=cmd_vel'],
            output='screen',
            condition=IfCondition(use_teleop)
        )]
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_teleop,
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        teleop,
    ])
