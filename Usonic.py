import asyncio
import websockets
import RPi.GPIO as GPIO
import time
import json  # Importamos el módulo JSON

# Definir pines de los tres sensores HC-SR04
SENSORS = {
    "Left": {"TRIG": 22, "ECHO": 23},
    "Right": {"TRIG": 4, "ECHO": 5},
    "Rear": {"TRIG": 24, "ECHO": 25}
}

# Configurar la Raspberry Pi
GPIO.setmode(GPIO.BCM)
for sensor in SENSORS.values():
    GPIO.setup(sensor["TRIG"], GPIO.OUT)
    GPIO.setup(sensor["ECHO"], GPIO.IN)

# Almacenar clientes WebSocket conectados
connected_clients = set()

def medir_distancia(TRIG, ECHO):
    """Mide la distancia utilizando un sensor ultrasónico HC-SR04."""
    GPIO.output(TRIG, False)
    time.sleep(0.05)  # Pequeña pausa para estabilizar el sensor

    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # Pulso de 10us
    GPIO.output(TRIG, False)
    
    inicio_pulso = time.time()
    timeout = inicio_pulso + 0.02  # Tiempo máximo de espera (20ms)

    while GPIO.input(ECHO) == 0:
        inicio_pulso = time.time()
        if inicio_pulso > timeout:
            return None  # Salir si no recibe respuesta en 20ms
    
    fin_pulso = time.time()
    timeout = fin_pulso + 0.02  # Otro timeout para evitar bloqueos

    while GPIO.input(ECHO) == 1:
        fin_pulso = time.time()
        if fin_pulso > timeout:
            return None  # Salir si se pasa del tiempo de espera
    
    # Calcular distancia
    duracion_pulso = fin_pulso - inicio_pulso
    distancia = (duracion_pulso * 34300) / 2  # Convertir a cm
    
    # Si la distancia es mayor a 400 cm (fuera del rango del sensor), se descarta
    if distancia < 2 or distancia > 400:
        return None
    return distancia

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
    """Ejecuta el servidor WebSocket y la transmisión de datos ultrasónicos en paralelo."""
    server = await websockets.serve(handle_client, "0.0.0.0", 5400)
    print("✅ Servidor WebSocket en ejecución en el puerto 5300...")
    
    await asyncio.gather(
        server.wait_closed(),
        send_ultrasonic_data()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ Cerrando servidor...")
        GPIO.cleanup()
