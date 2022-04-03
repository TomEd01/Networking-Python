import sys
import socket
import threading
def server_loop(local_host,local_port,remote_host,remote_port,receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host,local_port))
    except:
        print ("[!!] Failed to listen on %s:%d" % (local_host,local_port))
        print ("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(0)
    print ("[*] Listening on %s:%d" % (local_host,local_port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        # Imprimir la información de conexión local
        print ("[==>] Received incoming connection from %s:%d" % (addr[0],addr[1]))
        # Inicie un hilo para hablar con el host remoto
        proxy_thread = threading.Thread(target=proxy_handler,args=(client_socket,remote_host,remote_port,receive_first))
        proxy_thread.start()
def main():
    # No hay un análisis sofisticado de línea de comandos aquí
    if len(sys.argv[1:]) != 5:
        print ("Usage: ./proxy.py [localhost] [localport] [remotehost] [remoteport] [receive_first]")
        print ("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    # Configurar parámetros de escucha locales
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])
    # Configurar objetivo remoto
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])
    # Esto le dice a su proxy que se conecte y reciba datos
    # Antes de enviar al host remoto
    receive_first = sys.argv[5]
    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False
    # Ahora gira nuestro enchufe de escucha
    server_loop("127.0.0.1",900,"10.12.132.1",900,True)
def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # Conectarse al host remoto
    remote_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    remote_socket.connect((remote_host,remote_port))
    # Reciba datos del extremo remoto si es necesario
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)
        # Envíalo a nuestro controlador de respuestas.
        remote_buffer=response_handler(remote_buffer)
        # Si tenemos datos para enviar a su cliente local, envíelo
        if len(remote_buffer):
            print ("[<==] Sending %d bytes to localhost." % len(remote_buffer))
            client_socket.send(remote_buffer)
            # Ahora vamos a hacer un bucle y leer desde local,
            # Enviar a remoto, enviar a local
            # Enjuagar, lavar, repetir
            while True:
                # Leer del host local
                local_buffer = receive_from(client_socket)
                if len(local_buffer):
                    print ("[==>] Received %d bytes from localhost." % len(local_buffer))
                    hexdump(local_buffer)
                    # Envíalo a nuestro gestor de solicitudes.
                    local_buffer = request_handler(local_buffer)
                    # Enviar los datos al host remoto
                    remote_socket.send(local_buffer)
                    print ("[==>] Sent to remote.")
                # Reciba la respuesta
                remote_buffer = receive_from(remote_socket)
                if len(remote_buffer):
                    print ("[<==] Received %d bytes from remote." % len(remote_buffer))
                    hexdump(remote_buffer)
                    # Enviar a nuestro controlador de respuesta
                    remote_buffer = response_handler(remote_buffer)
                    # Enviar la respuesta al socket local
                    client_socket.send(remote_buffer)
                    print ("[<==] Sent to localhost.")
                # Si no hay más datos en ninguno de los lados, cierre las conexiones
                if not len(local_buffer) or not len(remote_buffer):
                    client_socket.close()
                    remote_socket.close()
                    print ("[*] No more data. Closing connections.")
                    break
# Esta es una bonita función de volcado hexadecimal tomada directamente de
# Los comentarios aquí:
# http://code.activestate.com/recipes/142812-hex-dumper/
def hexdump(src, length=16):
    result = []
    digits = 4 if isinstance(src, unicode) else 2
    for i in range(0, len(src), length):
        s = src[i:i+length]
        hexa = b' '.join(["%0*X" % (digits, ord(x)) for x in s])
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.' for x in s])
        result.append( b"%04X %-*s %s" % (i, length*(digits + 1), hexa, text) )
    print (b'\n'.join(result))
def receive_from(connection):
    buffer = ""
    # Establecemos un tiempo de espera de 2 segundos; depende de tu
    # Objetivo, esto puede necesitar ser ajustado
    connection.settimeout(2)
    try:
        # Siga leyendo en el búfer hasta que
        # No hay mas datos
        # O terminamos el tiempo
        while True:
            data = connection.recv(4096)
            if not data:
                break
        buffer += data
    except:
        pass
    return buffer
# Modificar cualquier solicitud destinada al host remoto
def request_handler(buffer):
    # Realizar modificaciones de paquetes
    return buffer
# Modificar cualquier solicitud destinada al host remoto
def response_handler(buffer):
    # Realizar modificaciones de paquetes
    return buffer
main()