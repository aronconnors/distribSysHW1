import sys
import socket
import selectors
import types
import time
import threading

sel = selectors.DefaultSelector()
message = "start"

# Establish connections, register the socket and its associated data
def start_connections(host, port):
    server_addr = (host, port)
    print(f"Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(server_addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        message=message,
        outb=b"",
    )
    sel.register(sock, events, data=data)

# Function constantly running to send and recieve data with the server
def service_connection(key, mask):
     sock = key.fileobj
     data = key.data
     # handle events where data is received from server
     if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        # specific case for closing connecions
        if recv_data.decode('utf-8') == 'Goodbye':
            print(recv_data.decode('utf-8'))
            print("\nClosing connection with server")
            sel.unregister(sock)
            sock.close()
        elif recv_data:
            print('\n'+recv_data.decode('utf-8')+'\n')
    # handle events where data is sent to server
     if mask & selectors.EVENT_WRITE:
        # if an outbound message is waiting, put it in outb
        if not data.outb and data.message:
            data.outb = data.message.encode('utf-8')
            data.message = None
        # if there is data in outb, send as much of it as we can
        if data.outb:
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

# input threading
def user_input(data):
    while True:
        data.message = input()

# ensure the client is started with proper arguments
if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <host> <port>")
    sys.exit(1)

host, port = sys.argv[1:3]
start_connections(host, int(port))

try:
    # threading to avoid input locking command line
    key = list(sel.get_map().values())[0]
    data = key.data
    input_thread = threading.Thread(target=user_input, args=(data,))
    input_thread.daemon = True
    input_thread.start()
    # continuously service the connections
    while True:
        events = sel.select(timeout=1)
        if events:
            for key, mask in events:
                service_connection(key, mask)
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()