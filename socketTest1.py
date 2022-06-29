from random import randint
import socket
import time
import json

HOST = '10.0.0.2'  # The server's hostname or IP address
#PORT = 65432        # The port used by the server
SOURCE_PORT, DESTINATION_PORT = 31420, 65432
packet=[]
packet.append(12345)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('0.0.0.0', SOURCE_PORT))
    s.connect((HOST, DESTINATION_PORT))
    while True:

        packet.append(randint(500, 5000))
        sendthis = json.dumps(packet)

        print(sendthis)
        s.sendall(bytes(sendthis, encoding="utf-8"))

        data = s.recv(1024)

        print('Received', data)
        time.sleep(2)
        packet.pop(1)

