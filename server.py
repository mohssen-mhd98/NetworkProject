import socket
import threading
"""
s = socket.socket("Network Layer Protocol", "Transport Layer Protocol")
s.bind(HOST, PORT) //
"""
PORT = 7447
MESSAGE_LENGTH_SIZE = 64
ENCODING = "utf-8"


def main():
    address = socket.gethostbyname(socket.gethostname())
    host_information = (address, PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(host_information)
    print("[Server strats] Server is starting...")
    start(s)


def start(sock):
    sock.listen()
    while True:
        connection, address = sock.accept()  # Gets connection and address of client
        t = threading.Thread(target=handle_client, args=(connection, address))
        t.start()


def handle_client(conn, addr):
    print("[NEW CONNECTION] connected from {}".format(addr))
    connected = True

    while connected:
        message_length = int(conn.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        msg = conn.recv(message_length).decode(ENCODING)

        print("[MESSAGE RECEIVED] {}".format(msg))

        if msg == "DISCONNECT":
            connected = False
    conn.close()


if __name__ == '__main__':
    main()
