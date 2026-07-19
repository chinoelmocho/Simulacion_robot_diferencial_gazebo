import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math

class NavigationController(Node):
    def __init__(self):
        super().__init__('navigation_controller')

        # Publicador de velocidad
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Suscriptor de odometría
        self.odom_sub = self.create_subscription(
            Odometry, '/wheel/odometry', self.odom_callback, 10
        )

        # Estado del robot
        self.xr = 0.0
        self.yr = 0.0
        self.phir = 0.0

        # ===== DEFINIR WAYPOINTS AQUÍ =====
        # Puedes cambiar estos puntos fácilmente
        self.waypoints = [
            (0.0, 1.0),   # Punto 1
            (1.0, 1.0),   # Punto 2
            (1.0, 0.0),   # Punto 3
            (2.0, 0.0),   # Punto 4
            (3.0, 0.0)    # Punto 5 - regreso al origen
        ]
        # ==================================

        self.current_waypoint_idx = 0
        self.xd = self.waypoints[0][0]
        self.yd = self.waypoints[0][1]
        self.phid = 0.0
        
        # Tiempo independiente para cada waypoint usando el reloj de ROS2
        self.waypoint_start_time = None  # Se inicializa en el primer ciclo
        
        # Bandera para saber si terminó todos los puntos
        self.mission_complete = False

        # Timer para control a 20 Hz
        self.timer = self.create_timer(0.05, self.control_loop)

        self.get_logger().info(f"Navegación iniciada con {len(self.waypoints)} waypoints")
        self.get_logger().info(f"Cada waypoint tiene control de 8 segundos (0-5s ascendente, 5-8s descendente)")
        self.get_logger().info(f"Waypoint 1/{len(self.waypoints)}: ({self.xd:.2f}, {self.yd:.2f})")

    def odom_callback(self, msg):
        self.xr = msg.pose.pose.position.x
        self.yr = msg.pose.pose.position.y
        # Extraer yaw del quaternion
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.phir = math.atan2(siny_cosp, cosy_cosp)

    def distance_to_goal(self):
        """Calcula la distancia al punto objetivo actual"""
        return math.sqrt((self.xd - self.xr)**2 + (self.yd - self.yr)**2)

    def next_waypoint(self):
        """Avanza al siguiente waypoint si hay disponible"""
        if self.current_waypoint_idx < len(self.waypoints) - 1:
            self.current_waypoint_idx += 1
            self.xd = self.waypoints[self.current_waypoint_idx][0]
            self.yd = self.waypoints[self.current_waypoint_idx][1]
            self.waypoint_start_time = self.get_clock().now()  # REINICIAR tiempo para nuevo waypoint
            self.get_logger().info(f"\n{'='*50}")
            self.get_logger().info(f"Waypoint {self.current_waypoint_idx + 1}/{len(self.waypoints)}: ({self.xd:.2f}, {self.yd:.2f})")
            self.get_logger().info(f"Iniciando ciclo de 8 segundos...")
            self.get_logger().info(f"{'='*50}\n")
            return True
        else:
            if not self.mission_complete:
                self.get_logger().info(f"\n{'='*50}")
                self.get_logger().info("🎯 ¡MISIÓN COMPLETADA! Todos los waypoints alcanzados.")
                self.get_logger().info(f"{'='*50}\n")
                self.mission_complete = True
            return False

    def control_loop(self):
        # Inicializar tiempo en el primer ciclo (cuando ROS2 ya está listo)
        if self.waypoint_start_time is None:
            self.waypoint_start_time = self.get_clock().now()
            self.get_logger().info("Tiempo de simulación inicializado")
        
        # Si ya completó todos los waypoints, detener el robot
        if self.mission_complete:
            twist = Twist()
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.cmd_pub.publish(twist)
            return

        # Calcular tiempo transcurrido desde inicio del waypoint actual (en segundos)
        current_time = self.get_clock().now()
        waypoint_time = (current_time - self.waypoint_start_time).nanoseconds / 1e9

        # Verificar si pasaron 8 segundos para este waypoint
        if waypoint_time >= 8.0:
            self.get_logger().info(f"Tiempo completado para waypoint {self.current_waypoint_idx + 1}")
            if not self.next_waypoint():
                return

        # --- Algoritmo de control ---
        xp = self.xd - self.xr
        yp = self.yd - self.yr
        l = math.sqrt(xp**2 + yp**2)
        beta = math.atan2(yp, xp) - self.phir
        psi = math.atan2(yp, xp)

        k1 = 1.5
        k2 = 2.0
        q2 = 0.2
        epsilon = 1e-6

        v_raw = k1 * l * math.cos(beta)

        if abs(beta) < epsilon:
            w_raw = k2 * beta
        else:
            w_raw = ((k1 / beta) * math.cos(beta) * math.sin(beta) * (beta + q2 * psi)) + k2 * beta

        # ===== SUAVIZADO ASCENDENTE: 0 a 5 segundos =====
        epsilon_s = 0.001
        k_s = math.pi
        T = 5.0
        
        if waypoint_time < T:
            theta = ((math.pi - 2*epsilon_s) / T) * waypoint_time - (math.pi/2 - epsilon_s)
            arg = -k_s * math.tan(theta)
            arg = max(min(arg, 50.0), -50.0)
            s = 1.0 / (1.0 + math.exp(arg))
        else:
            s = 1.0  # Ya pasó los 5 segundos

        # ===== SUAVIZADO DESCENDENTE: 5 a 8 segundos =====
        T2_start = 5.0
        T2_end = 8.0
        T2 = T2_end - T2_start  # 3 segundos
        
        if waypoint_time < T2_start:
            s2 = 1.0  # Antes de los 5s, va a máxima velocidad
        elif waypoint_time >= T2_end:
            s2 = 0.0  # Después de 8s, detenido
        else:
            # Entre 5 y 8 segundos, desaceleración suave
            t_desc = waypoint_time - T2_start  # Tiempo relativo 0-3s
            theta2 = ((math.pi - 2*epsilon_s) / T2) * t_desc - (math.pi/2 - epsilon_s)
            arg2 = math.tan(theta2)
            arg2 = max(min(arg2, 50.0), -50.0)
            s2 = 1.0 / (1.0 + math.exp(arg2))

        # Velocidades finales
        v = s * s2 * v_raw
        w = s * s2 * w_raw

        # Publicar en /cmd_vel
        twist = Twist()
        twist.linear.x = v
        twist.angular.z = w
        self.cmd_pub.publish(twist)

        # Info en consola
        distance = self.distance_to_goal()
        self.get_logger().info(
            f"WP{self.current_waypoint_idx + 1} | t={waypoint_time:.2f}s | "
            f"Pos: ({self.xr:.2f}, {self.yr:.2f}) | Dist: {distance:.2f}m | "
            f"s={s:.3f}, s2={s2:.3f} | v={v:.2f}, w={w:.2f}"
        )

def main(args=None):
    rclpy.init(args=args)
    node = NavigationController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()