from dynamixel_sdk import *

PORTS = ['/dev/ttyUSB0', '/dev/ttyUSB1']

for p in PORTS:
    print(f"Probando {p}")
    portHandler = PortHandler(p)
    if not portHandler.openPort():
        print("  No se pudo abrir.")
        continue

    portHandler.setBaudRate(57600)
    packetHandler = PacketHandler(1.0)

    dxl_id = 1
    addr = 500   # Present Position

    dxl_present, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(
        portHandler, dxl_id, addr)

    if dxl_comm_result == 0:
        print(f"  OK. Servo responde. Posición: {dxl_present}")
    else:
        print("  No responde.")

    portHandler.closePort()


def cleanup(self):
    self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    self.portHandler.closePort()
    print("✅ Servo deshabilitado y puerto cerrado.")