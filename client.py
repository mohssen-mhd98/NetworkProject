import socket

PORT = 7447
MESSAGE_LENGTH_SIZE = 64
ENCODING = "utf-8"


def main():
    address = socket.gethostbyname(socket.gethostname())
    host_information = (address, PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(host_information)
    print("[Client connects] Client is connecting...")
    message = ""
    while message != "DISCONNECT":
        message = input()
        send_message(s, message)


def send_message(client, message):
    msg = message.encode()
    msg_length = len(msg)
    msg_length = str(msg_length).encode(ENCODING)
    msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))

    client.send(msg_length)
    client.send(msg)


if __name__ == '__main__':
    main()
