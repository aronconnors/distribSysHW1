# more detailed code in the onenote

import sys
import socket
import selectors
import types
import time

sel = selectors.DefaultSelector()
message = "start"

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

def service_connection(key, mask):
     sock = key.fileobj
     data = key.data
     if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data.decode('utf-8') == 'Goodbye':
            print(recv_data.decode('utf-8'))
            print("Closing connection with server")
            sel.unregister(sock)
            sock.close()
        elif recv_data:
            print(recv_data.decode('utf-8'))
            data.message = input("\nEnter a command: ")
     if mask & selectors.EVENT_WRITE:
        if not data.outb and data.message:
            data.outb = data.message.encode('utf-8')
            data.message = None
        if data.outb:
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <host> <port>")
    sys.exit(1)

host, port = sys.argv[1:3]
start_connections(host, int(port))

try:
    while True:
        events = sel.select(timeout=1)
        if events:
            for key, mask in events:
                service_connection(key, mask)
        # Check for a socket being monitored to continue.
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()