import socket

target_host = "www.google.com"
target_port = 80

#crear un objepto para conectar
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#conectamos el cliente
client.connect((target_host,target_port))

#enviamos los datos
client.send("GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

#recivimos los datos
response = client.recv(4096)

print(response)