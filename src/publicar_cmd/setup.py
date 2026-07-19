from setuptools import find_packages, setup

package_name = 'publicar_cmd'

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
    maintainer='chino',
    maintainer_email='chino@todo.todo',
    description='Nodos de control del robot Bobert: publicacion de velocidad, lectura de odometria y navegacion por waypoints con un controlador basado en Lyapunov',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'publicar_vel = publicar_cmd.Publicar:main',
            'leer_Odom = publicar_cmd.suscriber_odom:main',
            'control= publicar_cmd.navegation_control:main',
        ],
    },
)
