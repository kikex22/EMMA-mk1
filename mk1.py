import asyncio
import websockets
import json
from flask import Flask, Response
from car import go_start, go_stop, reverse_start, reverse_stop, left_start, left_stop, right_start, right_stop
from lidar2 import LIDAR
from mpu import read_mpu
from camara import generar_frames
from Usonic import medir_distancia, SENSORS
import RPi.GPIO as GPIO
import time


app = Flask(__name__)


# Almacenar clientes conectados
connected_clients = set()

# Función para manejar los mensajes WebSocket (Control de los motores)
async def handle_message(websocket, path):
    """Maneja los mensajes entrantes de los clientes y controla los motores."""
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"📩 Mensaje recibido: {message}")
            
            if message == "GoStart":
                go_start()
            elif message == "GoStop":
                go_stop()
            elif message == "ReverseStart":
                reverse_start()
            elif message == "ReverseStop":
                reverse_stop()
            elif message == "LeftStart":
                left_start()
            elif message == "LeftStop":
                left_stop()
            elif message == "RightStart":
                right_start()
            elif message == "RightStop":
                right_stop()
            
    except websockets.exceptions.ConnectionClosed:
        print("⚠ Cliente desconectado")
    finally:
        connected_clients.remove(websocket)
        go_stop()

async def send_lidar_data():
    """Envía datos del LiDAR a los clientes conectados de forma periódica."""
    while True:
        if connected_clients:
            lidar_data = LIDAR()  # Lee datos LiDAR
            message = json.dumps({"lidar": lidar_data})  # Formatear los datos en JSON
            print(f"📡 Enviando LiDAR por WebSockets: {message}")  # Agregar este log
            await asyncio.gather(*(ws.send(message) for ws in connected_clients))
        
        await asyncio.sleep(1)  # Ajusta el tiempo según necesidad

async def send_ultrasonic_data():
    """Envía mediciones de sensores ultrasónicos a los clientes conectados cada 500ms."""
    while True:
        if connected_clients:
            ultrasonic_data = {}
            for name, pins in SENSORS.items():
                distance = medir_distancia(pins["TRIG"], pins["ECHO"])
                ultrasonic_data[name] = f"{distance:.2f} cm" if distance is not None else "Fuera de rango"

            # Convertimos el mensaje a formato JSON
            message = json.dumps({"ultrasonic": ultrasonic_data})
            await asyncio.gather(*(ws.send(message) for ws in connected_clients))
            print(f"📡 Enviando ultrasónicos: {message}")

        await asyncio.sleep(0.5)  # Enviar datos cada 500ms

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


# Ruta para la transmisión de video
@app.route('/video_feed')
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Función principal que ejecuta el servidor WebSocket, la transmisión LiDAR y el servidor Flask en paralelo
async def main():
    """Ejecuta el servidor WebSocket, la transmisión LiDAR y el servidor Flask en paralelo."""
    websocket_server = await websockets.serve(handle_message, "0.0.0.0", 5400)
    print("✅ Servidor WebSocket en ejecución en el puerto 5300...")
    
    loop = asyncio.get_running_loop()
    flask_future = loop.run_in_executor(None, app.run, "0.0.0.0", 5000, False, True)
    
    await asyncio.gather(
        websocket_server.wait_closed(),
        send_lidar_data(),
        send_ultrasonic_data(),
        send_mpu_data(),
        flask_future
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ Cerrando servidor...")
        GPIO.cleanup()
