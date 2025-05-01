import os
import time
import cv2
from flask import Flask, Response
from picamera2 import Picamera2

app = Flask(__name__)

# Función para liberar la cámara antes de iniciarla (evita bloqueos)
def liberar_camara():
    os.system("fuser -k /dev/video0")

# Liberamos la cámara antes de iniciar Flask
liberar_camara()

# Iniciar la cámara una sola vez
picam2 = Picamera2()

# Configurar la cámara para capturar en YUV420
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "YUV420"})
picam2.configure(config)

# Evitar fluctuaciones de FPS


picam2.start()

# Variables para calcular FPS
frame_count = 0
start_time = time.time()

def generar_frames():
    """Captura frames de la cámara y los envía en formato JPEG sin límite de FPS."""
    global frame_count, start_time

    while True:
        frame = picam2.capture_array("main")  # Captura en YUV420
        frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)  # Convertir a BGR para procesamiento
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
        frame_bytes = buffer.tobytes()

        # Contador de FPS
        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time > 1:  # Cada segundo
            fps = frame_count / elapsed_time
            print(f"🔵 FPS: {fps:.2f}")
            frame_count = 0
            start_time = time.time()

        # Enviar el frame en formato de streaming sin límite de FPS
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=False, threaded=True)