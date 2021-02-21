import socket
from threading import Thread
import time

PORT = 7447
MESSAGE_LENGTH_SIZE = 1024
ENCODING = "utf-8"
CONNECT = True

FILE_NAME = ""
PATH = ""
CLIENT_EXIST = True


def main():
    address = socket.gethostbyname(socket.gethostname())
    host_information = (address, PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(host_information)
    print("[Client connects] Client is connecting...")

    message = ""
    while message != "Accepted":
        name = input("Enter your name\n")
        send_message(s, name)

        message_length = int(s.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        message = s.recv(message_length).decode(ENCODING)

        if message == "Duplicate Username":
            print("Your username is duplicate...Please try a different username. ")

    get_list(s)

    # make a thread that listens for messages to this client & print them
    t = Thread(target=listen_for_messages, args=(s,))

    # make the thread daemon so it ends whenever the main thread ends
    t.daemon = True
    # start the thread
    t.start()

    message = ""
    while message != "DISCONNECT":
        global CLIENT_EXIST
        CLIENT_EXIST = True
        message = input("Enter name of person you want to send message to it. And if you wanna left enter "
                        "\"DISCONNECT\" command. \n")
        send_message(s, message)
        time.sleep(1)

        if message != "DISCONNECT" and CLIENT_EXIST:
            chat(message, s)

        elif message == "DISCONNECT":
            global CONNECT
            CONNECT = False

        elif not CLIENT_EXIST:
            print("Your desired person is not exist!....try another person")


def send_message(client, message):
    msg = message.encode()
    msg_length = len(msg)
    msg_length = str(msg_length).encode(ENCODING)
    msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))

    client.send(msg_length)
    client.send(msg)


def chat(person_name, s):
    message = ""
    print("you can send message to {} now.\n".format(person_name))

    while message != "Quit":
        print("You can send text message to someone with command \"Chat\" or send file with \"Send file\" command")
        message = input("What you want to do?\n")
        send_message(s, message)

        if message == "Send file":
            global FILE_NAME
            FILE_NAME = input("Enter file name (with its format):\n")
            global PATH
            PATH = input("Enter file directory:\n")
            send_message(s, FILE_NAME)


            # send_file()

        elif message == "Chat":
            # person_name = input("Who do you like to chat with? Enter its name.\n")
            # send_message(s, person_name)
            str_msg(s)

        else:
            print("Wrong command!! please try again with any of these commands:")
            print("Chat\tSend file\tQuit")


def str_msg(client):
    message = ""
    print("Type something for sending...\n")
    while message != "Quit":
        message = input()
        msg = message.encode()
        msg_length = len(msg)
        msg_length = str(msg_length).encode(ENCODING)
        msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))

        client.send(msg_length)
        client.send(msg)

        # if message != "Quit":
        #     message_length = int(client.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        #     msg = client.recv(message_length).decode(ENCODING)
        #     print(msg)


def listen_for_messages(client):
    while CONNECT:
        message_length = int(client.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        # print("***{}".format(message_length))
        message = client.recv(message_length).decode(ENCODING)

        if message == "Quit":
            send_message(client, "Quit")
            send_message(client, "Quit")

        if message == "Person is not exist":
            global CLIENT_EXIST
            CLIENT_EXIST = False

        # Server receive from client
        elif message == "RECV FILE":
            send_file(client, PATH, FILE_NAME)
        # Server sent to client
        elif message == "SEND FILE":
            file_name_length = int(client.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
            file_name = client.recv(file_name_length).decode(ENCODING)
            send_message(client, "RECEIVE FILE")
            send_message(client, file_name)
            receive_file(client, file_name)
        if message != "SEND FILE" and message != "Quit" and message != "RECV FILE":
            print("\n" + message)


def receive_file(tcp_connection, file_name):
    addr = file_name
    file = open(addr, 'wb')
    try:
        msg_length = tcp_connection.recv(MESSAGE_LENGTH_SIZE)
        msg_length = int(msg_length.decode(ENCODING))
        print(msg_length)
        data = tcp_connection.recv(msg_length)
        file.write(data)
        print("Receiving...")
    except ConnectionResetError:
        pass
    while True:
        try:
            data_length = int(tcp_connection.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
            data = tcp_connection.recv(data_length)
            print("Receiving...")
        except ConnectionError:
            break
        try:
            if data.decode(ENCODING) == 'Send Completed':
                break
        except UnicodeDecodeError:
            pass
        file.write(data)

    file.close()
    print("Done Receiving")
    response = 'Done:' + file_name
    response = response.encode()
    msg_length = len(response)
    msg_length = str(msg_length).encode(ENCODING)
    msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))
    try:
        tcp_connection.send(msg_length)
        tcp_connection.send(response)
    except ConnectionResetError:
        pass


def send_file(tcp_connection, path, file_name):
    addr = path + '\\' + file_name
    print(addr)
    with open(addr, 'rb') as file:
        data = file.read(MESSAGE_LENGTH_SIZE)

        print('Sending...', data)
        while data:
            msg_length = min(len(data), MESSAGE_LENGTH_SIZE)
            msg_length = str(msg_length).encode(ENCODING)
            msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))
            tcp_connection.send(msg_length)
            tcp_connection.send(data)
            print('Sending...')

            data = file.read(MESSAGE_LENGTH_SIZE)

    print("Done Sending")
    response = 'Send Completed'
    msg_length = len(response)
    msg_length = str(msg_length).encode(ENCODING)
    msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))
    tcp_connection.send(msg_length)
    try:
        tcp_connection.send(response.encode(ENCODING))
        msg_length = int(tcp_connection.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        resp_parts = tcp_connection.recv(msg_length).decode(ENCODING).split(':')
        print('File', resp_parts, 'Sent Successfully')

    except ConnectionResetError:
        pass


def get_list(c_socket):
    list_size_length = int(c_socket.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
    # print("***{}".format(message_length))
    list_size = c_socket.recv(list_size_length).decode(ENCODING)
    i = int(list_size)
    print("You can contact to:")
    while i > 0:
        cnmae_length = int(c_socket.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        # print("***{}".format(message_length))
        cname = c_socket.recv(cnmae_length).decode(ENCODING)
        print(cname, "\t", end=" ")
        i = i - 1
    print()


if __name__ == '__main__':
    main()
