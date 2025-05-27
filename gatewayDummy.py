import socket

# Configuración
IP_SERVIDOR = '127.0.0.1'  #IP server
PUERTO_SERVIDOR = 4000

# Crear socket TCP
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
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
    pass
