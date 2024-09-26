#for more detailed information about this code, go to the onenote file socket programming
#not quite sure if all the code is in the right order as of right now

import sys
import socket
import selectors
import types
import json

sel = selectors.DefaultSelector()
activeConnections = {}

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    newId = 10000
    while True:
        if newId in activeConnections:
            newId += 1
        else:
            data = types.SimpleNamespace(addr=addr, id=newId, inb=b"", outb=b"")
            activeConnections[newId] = addr
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
            sel.register(conn, events, data=data)
            break

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            if recv_data.decode('utf-8') == 'start':
                data.outb += str(key.data.id).encode('utf-8')
            if recv_data.decode('utf-8') == 'list':
                    users = ''
                    for key1, fileObj in sel.get_map().items():
                        if fileObj.data:
                            users = users + str(fileObj.data.id) + ', '
                    data.outb += users[:-2].encode('utf-8')
            if recv_data.decode('utf-8') == 'exit':
                data.outb += 'Goodbye'.encode('utf-8')
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            if data.outb.decode('utf-8') == "Goodbye":
                print(f"Saying goodbye to {data.addr}")
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()
            else:
                print(f"Echoing {data.outb.decode('utf-8')} to {data.addr}")
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]


host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()