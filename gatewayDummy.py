import socket
import time
import signal
import random

# Configuración
IP_SERVIDOR = '192.168.1.44'  #IP server
PUERTO_SERVIDOR = 4000

GATEWAY_STORE_CID_EVENT = "STORE_CID {0} pruebaDummy{1}"

# Crear socket TCP
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def handler_sigint(signum, frame):
    print("\n Señal SIGINT recibida. Cerrando programa...")
    exit(0)

try:
    signal.signal(signal.SIGINT, handler_sigint)
    
    # Intentar conectar con el servidor
    print("conectando al server")
    cliente.connect((IP_SERVIDOR, PUERTO_SERVIDOR))
    print(f"Conectado al servidor en {IP_SERVIDOR}:{PUERTO_SERVIDOR}")

except ConnectionRefusedError:
    print("No se pudo conectar al servidor.")
except Exception as e:
    print("Ocurrió un error:", e)

while(True):
    time.sleep(20)
    randNumber = random.randint(1, 500)
    msg = GATEWAY_STORE_CID_EVENT.format(randNumber,randNumber)
    binMsg = msg.encode('utf-8')
    print(msg)
    cliente.sendall(binMsg)
print("Fin del script!!")