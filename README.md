# 🚀 APP_LIDAR
Trabajo de grado
Sistema basado en ROS para adquisición y procesamiento de datos LiDAR en robot móvil P3AT, con arquitectura distribuida Robot–Cliente y API intermedia en Python.

---

## 📌 Descripción General

APP_LIDAR permite:

- Controlar robot móvil P3AT
- Obtener datos desde sensor LiDAR Hokuyo
- Exponer servicios mediante API en Python
- Ejecutar aplicación principal desde una laptop remota

Arquitectura general:

```
ROBOT (ROS Master + Sensores + Servicios)
        │
        │  Red ROS
        ▼
LAPTOP (API Server + Aplicación Principal)
```

---

# 🖥️ Requisitos del Sistema

## 🔹 Robot Móvil

- Ubuntu 20.04  
- ROS Noetic  
- rosaria  
- hokuyo_node  
- Python 3  
- Workspace catkin configurado  
- Hokuyo conectado en `/dev/ttyACM0`  
- Conectividad SSH  

## 🔹 Laptop Cliente

- Ubuntu 20.04  
- ROS Noetic  
- Python 3  
- `catkin_ws` configurado  
- pip3 instalado  

---

# 📦 Instalación

## 1️⃣ Clonar repositorio

En robot y laptop:

```bash
cd ~/catkin_ws/src
git clone https://github.com/Nickleon16/APP_LIDAR.git
cd ..
catkin_make
source devel/setup.bash
```

---

## 2️⃣ Instalar dependencias Python

Dentro del proyecto:

```bash
pip3 install -r requirements.txt
```

---

# 🌐 Configuración de Red

Verificar IP del robot:

```bash
ifconfig
```

IP esperada del robot:

```
192.168.3.102
```

Configurar variables ROS si es necesario.

En la laptop:

```bash
export ROS_MASTER_URI=http://192.168.3.102:11311
export ROS_IP=IP_DE_TU_LAPTOP
```

⚠️ Ambos equipos deben estar en la misma red.

---

# ▶️ Ejecución del Sistema

---

# 🔹 PASO 1 – Robot

Conectarse por SSH:

```bash
ssh p3at@192.168.3.102
```

Ejecutar:

```bash
cd ~/catkin_ws/src/APP_LIDAR
./start_robot.sh
```

Este script inicia automáticamente:

- roscore  
- RosAria  
- Hokuyo  
- lidar_servo_service_node.py  

---

# 🔹 PASO 2 – Laptop

```bash
cd ~/catkin_ws/src/APP_LIDAR/scripts
./start_client.sh
```

Este script inicia:

- api_server.py  
- main.py  

---

# 📂 Estructura del Proyecto

```
APP_LIDAR/
│
├── GUI/
│   ├── archivos para GUI
│
├── nubes/
│   ├── Ejemplos de capturas .pcd
│
├── odom/
│   ├── Ejemplo archivos odometria .csv
│
├── scripts/
│   ├── api_server.py
│   ├── main.py
│   ├── lidar_servo_service_node.py
│   ├── demas archivos .py
│
├── start_robot.sh
├── start_client.sh
├── requirements.txt
└── README.md
```

---

# 🛠️ Troubleshooting

## ❌ No conecta al ROS Master

Verificar variables:

```bash
echo $ROS_MASTER_URI
echo $ROS_IP
```

Ambos equipos deben apuntar correctamente al robot.

---

## ❌ Hokuyo no detectado

Verificar puerto:

```bash
ls /dev/ttyACM*
```

Si cambia el puerto, modificarlo en `start_robot.sh`.

---

## ❌ Permiso denegado en scripts

```bash
chmod +x start_robot.sh
chmod +x start_client.sh
```

---

# 📡 Puertos Utilizados

- ROS Master: 11311  
- API Server: (definir puerto si aplica)

---

# 👤 Autor

Nicolas Polindara Leon
nicolas.polindara@correounivalle.edu.co 
Proyecto APP_LIDAR