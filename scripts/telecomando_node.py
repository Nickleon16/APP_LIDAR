# telecomando_node.py

from PyQt5.QtWidgets import QWidget,  QLabel, QVBoxLayout
from PyQt5.QtCore import QObject, QEvent, Qt
from telecomando_ui import Ui_Form
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rospy

class TelecomandoWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.ui = Ui_Form()
        self.ui.setupUi(self)
            
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.rate = rospy.Rate(10)

        # Etiquetas para mostrar datos
        self.ui.posicionLabel.setText("Posición: (x, y, z)")
        self.ui.velocidadLabel.setText("Velocidad Lineal: 0.0 m/s | Angular: 0.0 rad/s")

        self.ui.avanzarPushButton.pressed.connect(self.avanzar)
        self.ui.avanzarPushButton.released.connect(self.stop)

        self.ui.reversaPushButton.pressed.connect(self.retroceder)
        self.ui.reversaPushButton.released.connect(self.stop)

        self.ui.izquierdaPushButton.pressed.connect(self.izquierda)
        self.ui.izquierdaPushButton.released.connect(self.stop)

        self.ui.derechaPushButton.pressed.connect(self.derecha)
        self.ui.derechaPushButton.released.connect(self.stop)        

        # TODO: Acceder a servidor de parametros ROS
        self.speed = 0.2  # m/s
        self.turn = 1.0   # rad/s

        self.installEventFilter(self)

        # Suscripciones
        self.cmd_vel_sub = rospy.Subscriber('/cmd_vel', Twist, self.cmd_vel_callback)
        self.odom_sub = rospy.Subscriber('/odom', Odometry, self.odom_callback)

    def avanzar(self):
        twist = Twist()
        twist.linear.x = self.speed
        self.pub.publish(twist)

    def retroceder(self):
        twist = Twist()
        twist.linear.x = -self.speed
        self.pub.publish(twist)

    def izquierda(self):
        twist = Twist()
        twist.angular.z = self.turn
        self.pub.publish(twist)

    def derecha(self):
        twist = Twist()
        twist.angular.z = -self.turn
        self.pub.publish(twist)

    def stop(self):
        self.pub.publish(Twist())

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:
            key = event.key()

            twist = Twist()
            if key == Qt.Key_W:
                twist.linear.x = self.speed
            elif key == Qt.Key_S:
                twist.linear.x = -self.speed
            elif key == Qt.Key_A:
                twist.angular.z = self.turn
            elif key == Qt.Key_D:
                twist.angular.z = -self.turn
            else:
                return False  # tecla no relevante

            self.pub.publish(twist)
            return True
        
        elif event.type() == QEvent.KeyRelease:
            key = event.key()            
            if key in [Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D]:
                self.stop()
                return True

        return super().eventFilter(obj, event)
    
    def odom_callback(self, msg):
        pos = msg.pose.pose.position        
        self.ui.posicionLabel.setText(f"Posición: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")

    def cmd_vel_callback(self, msg):
        lin = msg.linear
        ang = msg.angular
        self.ui.velocidadLabel.setText(f"Velocidad lineal: {lin.x:.2f} m/s | Angular: {ang.z:.2f} rad/s")
