import asyncio
import websockets
import json
from TfLunaI2C import TfLunaI2C
import time

# Inicializar el sensor
tf = TfLunaI2C()
tf.us = False  # Usar centímetros
tf.save()
tf.reboot()
time.sleep(2)

# Almacenar clientes conectados
connected_clients = set()

def LIDAR():
    try:
        data = tf.read_data()  # Supongamos que devuelve [120, 50, 25]
        if isinstance(data, list) and len(data) >= 3:
            
            return {
                "distance": data[0], 
                "amplitude": data[1], 
                "temperature": data[2]
            }  # Retorna un diccionario
        else:
            return {"distance": 0, "amplitude": 0, "temperature": 0}
    except Exception:
        return {"distance": 0, "amplitude": 0, "temperature": 0}

async def handle_message(websocket, path):
    """Maneja los mensajes entrantes de los clientes y permite que se conecten."""
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"📩 Mensaje recibido: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("⚠ Cliente desconectado")
    finally:
        connected_clients.remove(websocket)

async def send_lidar_data():
    """Envía datos del LiDAR a los clientes conectados de forma periódica."""
    while True:
        if connected_clients:
            lidar_data = LIDAR()  # Lee datos LiDAR
            message = json.dumps({"lidar": lidar_data})  # Formatear los datos en JSON
            await asyncio.gather(*(ws.send(message) for ws in connected_clients))
            print(f"📡 Enviando LiDAR: {message}")
        
        await asyncio.sleep(1)  # Ajusta el tiempo según necesidad

async def main():
    """Ejecuta el servidor WebSocket y el envío de datos LiDAR en paralelo."""
    websocket_server = await websockets.serve(handle_message, "0.0.0.0", 5400)
    print("✅ Servidor WebSocket en ejecución en el puerto 5400...")
    
    # Ejecutar la función de envío de LiDAR en paralelo
    await asyncio.gather(
        websocket_server.wait_closed(),
        send_lidar_data()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ Cerrando servidor...")
