import asyncio
import websockets
import RPi.GPIO as GPIO
import base64
import time
from picamera2 import Picamera2
import cv2

# Pines GPIO
IN1 = 17
IN2 = 27
ENA = 18
IN3 = 26
IN4 = 20
ENB = 19
ENC = 12
IN5 = 1
IN6 = 7
END = 13
IN7 = 6
IN8 = 16

# Configurar GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([IN1, IN2, ENA, IN3, IN4, ENB, IN5, IN6, ENC, IN7, IN8, END], GPIO.OUT)
GPIO.output(ENA, GPIO.HIGH)
GPIO.output(ENB, GPIO.HIGH)
GPIO.output(ENC, GPIO.HIGH)
GPIO.output(END, GPIO.HIGH)

# Función para detener todos los motores
def stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    GPIO.output(IN5, GPIO.LOW)
    GPIO.output(IN6, GPIO.LOW)
    GPIO.output(IN7, GPIO.LOW)
    GPIO.output(IN8, GPIO.LOW)

# Funciones de movimiento
def go_start():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    GPIO.output(IN5, GPIO.HIGH)
    GPIO.output(IN6, GPIO.LOW)
    GPIO.output(IN7, GPIO.HIGH)
    GPIO.output(IN8, GPIO.LOW)

def go_stop():
    stop()

def reverse_start():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    GPIO.output(IN5, GPIO.LOW)
    GPIO.output(IN6, GPIO.HIGH)
    GPIO.output(IN7, GPIO.LOW)
    GPIO.output(IN8, GPIO.HIGH)

def reverse_stop():
    stop()

def left_start():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    GPIO.output(IN5, GPIO.LOW)
    GPIO.output(IN6, GPIO.HIGH)
    GPIO.output(IN7, GPIO.HIGH)
    GPIO.output(IN8, GPIO.LOW)

def left_stop():
    stop()

def right_start():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    GPIO.output(IN5, GPIO.HIGH)
    GPIO.output(IN6, GPIO.LOW)
    GPIO.output(IN7, GPIO.LOW)
    GPIO.output(IN8, GPIO.HIGH)

def right_stop():
    stop()

# Función de manejo de WebSocket
async def handle_message(websocket, path):
    try:
        async for message in websocket:
            print(f"Mensaje recibido: {message}")

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
        print("Cliente desconectado")
        stop()

# Función principal
async def main():
    async with websockets.serve(handle_message, "0.0.0.0", 8080):
        print("Servidor WebSocket en ejecución en el puerto 8080...")
        await asyncio.Future()  # Mantener el servidor vivo

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Cerrando servidor y limpiando GPIO...")
        stop()
        GPIO.cleanup()
