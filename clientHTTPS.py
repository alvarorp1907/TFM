import requests
import random
import time

SERVER_IP = "192.168.1.44"
SERVER_PORT = "5000"
url = f'https://{SERVER_IP}:{SERVER_PORT}'

cert= (r'C:\Users\arpcr\OneDrive\Escritorio\dummyClientCertificates\client.cert',r'C:\Users\arpcr\OneDrive\Escritorio\dummyClientCertificates\client.key')

ca = r'C:\Users\arpcr\OneDrive\Escritorio\CAcertificates\ca.cert'

unixTime = str(time.time())
data = "SEND_TELEMETRY {Sensor1: {temp: 24,hum: 58, timestamp: 06062025-190200}, Sensor2: {temp: 30, hum: 60, timestamp: " + unixTime + "}}"
print(f"POST -> {data}")
response = requests.post(url, data=data, cert=cert, verify=ca)
print(f"RESPONSE: {response.status_code}->{response.text}")
    
while(True):
    time.sleep(60)
    unixTime = str(time.time())
    data = "SEND_TELEMETRY {Sensor1: {temp: 24,hum: 58, timestamp: 06062025-190200}, Sensor2: {temp: 30, hum: 60, timestamp: " + unixTime + "}}"
    print(f"POST -> {data}")
    response = requests.post(url, data=data, cert=cert, verify=ca)
    print(f"RESPONSE: {response.status_code}->{response.text}")
