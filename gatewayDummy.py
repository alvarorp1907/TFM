import socket
import time
import signal

# Configuración
IP_SERVIDOR = '127.0.0.1'  #IP server
PUERTO_SERVIDOR = 4000

GATEWAY_STORE_CID_EVENT = b"STORE_CID HASJASIAJAS pruebaDummy1"

# Crear socket TCP
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def handler_sigint(signum, frame):
    print("\n Señal SIGINT recibida. Cerrando programa...")
    exit(0)

try:
    signal.signal(signal.SIGINT, handler_sigint)
    
    # Intentar conectar con el servidor
    cliente.connect((IP_SERVIDOR, PUERTO_SERVIDOR))
    print(f"Conectado al servidor en {IP_SERVIDOR}:{PUERTO_SERVIDOR}")

    # Enviar mensaje
    # mensaje = "Hola servidor, soy el cliente."
    # cliente.sendall(mensaje.encode())

    # Recibir respuesta
    # respuesta = cliente.recv(1024)
    # print("Respuesta del servidor:", respuesta.decode())

except ConnectionRefusedError:
    print("No se pudo conectar al servidor.")
except Exception as e:
    print("Ocurrió un error:", e)

while(True):
    time.sleep(5)
    cliente.sendall(GATEWAY_STORE_CID_EVENT)
    break
print("Fin del script!!")