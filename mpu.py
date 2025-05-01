import smbus
import asyncio
import websockets
import json

# Dirección del MPU6050
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47

# Iniciar el bus I2C y activar el MPU6050
bus = smbus.SMBus(1)
bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)

# Almacenar clientes WebSocket conectados
connected_clients = set()

async def read_word(reg):
    """Lee un valor de 16 bits del MPU6050 de forma no bloqueante."""
    def read():
        high = bus.read_byte_data(MPU6050_ADDR, reg)
        low = bus.read_byte_data(MPU6050_ADDR, reg + 1)
        value = (high << 8) + low
        if value >= 0x8000:  # Convertir valores negativos
            value -= 0x10000
        return value

    return await asyncio.to_thread(read)  # Ejecuta en un hilo separado

async def read_mpu():
    """Lee los valores del acelerómetro y giroscopio del MPU6050."""
    try:
        accel_x = await read_word(ACCEL_XOUT_H)
        accel_y = await read_word(ACCEL_YOUT_H)
        accel_z = await read_word(ACCEL_ZOUT_H)
        gyro_x = await read_word(GYRO_XOUT_H)
        gyro_y = await read_word(GYRO_YOUT_H)
        gyro_z = await read_word(GYRO_ZOUT_H)

        mpu_data = {
            "accelerometer": {"x": accel_x, "y": accel_y, "z": accel_z},
            "gyroscope": {"x": gyro_x, "y": gyro_y, "z": gyro_z}
        }

        return mpu_data
    except Exception as e:
        print(f"⚠ Error en MPU6050: {e}")
        return None

async def send_mpu_data():
    """Envía mediciones del MPU6050 a los clientes conectados cada 500ms."""
    while True:
        if connected_clients:
            mpu_data = await read_mpu()
            if mpu_data:
                message = json.dumps({"mpu": mpu_data})
                await asyncio.gather(*(ws.send(message) for ws in connected_clients))
                print(f"📡 Enviando datos MPU6050: {message}")

        await asyncio.sleep(0.5)  # Enviar datos cada 500ms

async def handle_client(websocket, path):
    """Maneja la conexión WebSocket con los clientes."""
    connected_clients.add(websocket)
    try:
        async for _ in websocket:  # Mantener la conexión activa
            pass
    except websockets.exceptions.ConnectionClosed:
        print("⚠ Cliente WebSocket desconectado")
    finally:
        connected_clients.remove(websocket)

async def main():
    """Ejecuta el servidor WebSocket y la transmisión de datos MPU6050 en paralelo."""
    server = await websockets.serve(handle_client, "0.0.0.0", 5400)
    print("✅ Servidor WebSocket en ejecución en el puerto 5400...")

    await asyncio.gather(
        server.wait_closed(),
        send_mpu_data()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ Cerrando servidor...")
