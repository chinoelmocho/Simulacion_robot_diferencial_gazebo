import os
  
from ament_index_python.packages import get_package_share_directory
 
from launch_ros.parameter_descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
  
def generate_launch_description():
 
 
    model_arg = DeclareLaunchArgument(name='model', description='Absolute path to robot urdf file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    package_name = 'robot_description'
    pkg_share = FindPackageShare(package=package_name).find(package_name)
    pkg_gazebo_ros = FindPackageShare(package='gazebo_ros').find('gazebo_ros')


    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
        )

    robot_name_in_model = 'Bobert'

    # Get URDF via xacro

    urdf_file_name = 'Bobert.urdf'
    urdf = os.path.join(
        get_package_share_directory('robot_description'),
        'urdf',
        urdf_file_name
        )
    with open(urdf, 'r') as infp:
        robot_desc = infp.read()

    robot_description = {"robot_description": robot_desc}
 
 
    #rivz2
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        parameters=[{'use_sim_time': use_sim_time}],
    )
 
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters= [{'use_sim_time': use_sim_time, 'robot_description': robot_desc}] 
    )

    start_joint_state_publisher_cmd = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{'use_sim_time': use_sim_time}],
        name='joint_state_publisher',
    )
 

    world_path = os.path.join(
        get_package_share_directory('robot_description'),
        'worlds',
        'oficce_small.world'
        )

    spawn = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=["-topic", "/robot_description",
                    "-entity", robot_name_in_model,
                    "-x", '0.0',
                    "-y", '0.0',
                    "-z", '0.17',
                    "-Y", '0.0']
    )

    # Se incluye el launch propio de gazebo_ros (en vez de llamar al binario
    # 'gazebo' directamente) porque es el que exporta GAZEBO_MODEL_PATH /
    # GAZEBO_RESOURCE_PATH con el share/ de este paquete; sin eso Gazebo no
    # resuelve los "package://robot_description/meshes/..." del URDF y el
    # robot se spawnea sin mallas.
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_path, 'verbose': 'true'}.items()
        )
    slam_toolbox = ExecuteProcess(
        cmd=[
            'ros2', 'launch', 'slam_toolbox', 'online_async_launch.py',
            f'slam_params_file:={os.path.join(get_package_share_directory("robot_description"), "config", "mapper_params_online_async.yaml")}',
            'use_sim_time:=true'
        ],
        output='screen'
    )

    return LaunchDescription([
    declare_use_sim_time_cmd,
    robot_state_publisher_node,
    gazebo,
    rviz2,
    spawn,
    slam_toolbox,
])