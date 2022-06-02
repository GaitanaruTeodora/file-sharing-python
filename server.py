
from multiprocessing import connection
import socket
import threading
import json
import os

IP = "127.0.0.1"
PORT = 8095

conections = {}  # userii conectati
FORMAT = "utf-8"
SIZE = 1024

SERVER_DATA_PATH = "server_data/uploads/"
SERVER_DATA_USER_INFO = "server_data/users/"


def read_files():
    file = open(SERVER_DATA_USER_INFO+"files.json", "r")
    json_object = json.load(file)
    file.close()
    return json_object


def write_to_files(json_obj):
    file = open(SERVER_DATA_USER_INFO+"files.json", "w")
    json.dump(json_obj, file)
    file.close()


def read_continut(user, fisier):
    lines = ''
    with open(SERVER_DATA_PATH+user+"/"+fisier) as f:
        lines = f.readlines()

    rez = ''
    for line in lines:
        rez = rez + line + "\n"
    return rez


def read_users():
    file = open(SERVER_DATA_USER_INFO+"info.txt", "r")
    useri = {}
    for linie in file:

        useri[linie.split()[0]] = linie.split()[1]
    file.close()
    return useri


def registerUser(username, password):
    file = open(SERVER_DATA_USER_INFO+"info.txt", "a+")
    users = read_users()
    if username.strip() in users:
        file.close()
        return 0
    else:
        file.write(username)
        file.write(" ")
        file.write(password)
        file.write("\n")
    file.close()
    return 1


def loginUser(username, password):
    file = open(SERVER_DATA_USER_INFO+"info.txt", "a+")
    users = read_users()
    file.close()
    if username in users:

        if users[username] == password:
            return 0
    else:
        return 1


def get_users():
    global conections
    fis = read_files()
    output = ""
    for user in fis:
        rez = "@" + user+" "
        if user in conections:
            for fisier in fis[user]['fisiere']:
                rez = rez + "*"+fisier
            output = output + rez
    # print(output)
    for conn in conections:
        # print(conections[conn]['username']+"\n")
        conections[conn]['socket'].send(output.encode(FORMAT))


def handle_client(conexion, address):

    ok = 0
    try:
        while ok == 0:
            message = conexion.recv(SIZE).decode(FORMAT)
            data = message.split("@")

            cmd = data[0]

            if cmd == "REGISTER":
                try:
                    username = data[1]
                    password = data[2]
                    status = registerUser(username, password)
                    send_data = ""
                    if status == 0:
                        send_data = send_data + \
                            "Username {} folosit  !".format(username)
                    else:
                        send_data = send_data + "Te ai inregistrat cu succes"
                    print(send_data)
                    conexion.send(send_data.encode(FORMAT))
                except Exception as e:
                    print(e)

            elif cmd == 'LOGIN':
                username = data[1]
                password = data[2]
                status = loginUser(username, password)
                send_data = ""
                if status == 0:
                    send_data = send_data + \
                        "OK-LOGIN@Te ai logat cu succes {}".format(username)

                    conections[username] = {
                        "username": username,
                        "socket": conexion,
                        "fisiere": []
                    }
                    conexion.send(send_data.encode(FORMAT))

                    ok = 1
                    break
                else:
                    send_data = "ERROR@Username sau parola invalide"

                    conexion.send(send_data.encode(FORMAT))

        thread = threading.Thread(
            target=server_send, args=(conexion, username,))
        thread.start()

    except:
        try:
            conexion.close()
            conections.remove(conexion)
        except:
            pass


def server_send(conexion, username):
    global conections
    for conn in conections:
        if conexion != conections[conn]['socket']:
            conections[conn]['socket'].send(
                "Userul {} s-a conectat la server".format(username).encode(FORMAT))
    get_users()  # notifica clientul cand se produce o schimbare in lista de useri
    while True:
        message = conexion.recv(SIZE).decode(FORMAT)
       
        data = ''
        try:
            data = message.split("@")
        except:
            pass

        if message == 'LOGOUT':
            del conections[username]
            get_users()
            for conn in conections:
                if conexion != conections[conn]['socket']:
                    conections[conn]['socket'].send(
                        "Userul {} s-a deconectat de la server".format(username).encode(FORMAT))

            conexion.close()
            break
        if data[0] == 'DELETE':
            fis = data[1]
            os.remove(SERVER_DATA_PATH+username+"/"+fis)
            json_fisiere = read_files()
            json_fisiere[username]['fisiere'].remove(fis)
            write_to_files(json_fisiere)

            trimite_mesage(
                conexion, "Userul {} a sters fisierul {}".format(username, fis))
            get_users()

        if data[0] == 'RASPUNS':
            if data[1] == 'YES':
                json_fisiere = read_files()
                rasp = "Ai primit aprobare sa citesti fisierul {} \n Continut fisier :\n".format(
                    data[4])
                continut = read_continut(data[3], data[4])
                rasp = rasp + continut
                conections[data[2]]['socket'].send(rasp.encode(FORMAT))

            else:
                rasp = "Nu ai primit aprobare pentru citire \n"
                conections[data[2]]['socket'].send(rasp.encode(FORMAT))

        if data[0] == 'RASPUNS-DESCARC':
            if data[1] == 'YES':
                json_fisiere = read_files()
                rasp = "CONTINUT@{}@".format(data[4])
                continut = read_continut(data[3], data[4])
                rasp = rasp + continut
                conections[data[2]]['socket'].send(rasp.encode(FORMAT))

            else:
                rasp = "Nu ai primit aprobare pentru descarcare \n"
                conections[data[2]]['socket'].send(rasp.encode(FORMAT))

        if data[0] == 'APROB':
            # username = cel care solicita aprobarea, data[1] = username aprobator , data[2] = fisierul solicitat
            send_data = "APROB@{}@{}@{}@ Aprobi citirea fisierului {} de catre userul  ? YES == APROBARE >> {}".format(
                username, data[1], data[2], data[2], username)
            # ii trimit aprobarea userului aprobator
            conections[data[1]]['socket'].send(send_data.encode(FORMAT))
        if data[0] == 'DESCARC':
            send_data = "DESCARC@{}@{}@{}@ Aprobi descarcarea fisierului {} de catre userul ? YES == APROBARE >> {}".format(
                username, data[1], data[2], data[2], username)
            conections[data[1]]['socket'].send(send_data.encode(FORMAT))
        if data[0] == 'UPLOAD':

            fisiere_user = data[1].split("$")
            fisiere_user = [x for x in fisiere_user if x != '']
            json_fisiere = read_files()
            denumiri = "\n"
            if username not in json_fisiere:
                json_fisiere[username] = {
                    "fisiere": []
                }
            for idx, fis in enumerate(fisiere_user):
                data_split = fis.split("*")
                print("Data : {}".format(str(data_split)))
                den = data_split[0]
                denumiri = denumiri + str(idx+1)+" => "+den + '\n'
                continut = data_split[1]
                dir = SERVER_DATA_PATH+username
                os.makedirs(dir, exist_ok=True)
                filepath = os.path.join(dir+"/", den)
                with open(filepath, "w") as f:
                    f.write(continut)

                send_data = "\n File uploaded successfully.{}".format(username)
                if den not in json_fisiere[username]['fisiere']:
                    json_fisiere[username]['fisiere'].append(den)
                conexion.send("\n Ai incarcat fisierele {}".format(
                    denumiri).encode(FORMAT))
                print(send_data)
            write_to_files(json_fisiere)

            mesaj = "\n Userul {} a incarcat fisierele : {}  ".format(
                username, denumiri)
            trimite_mesage(conexion,  mesaj)
            get_users()

            # conn.send(send_data.encode(FORMAT))


def trimite_mesage(conexion, mesaj):
    for conn in conections:
        if conexion != conections[conn]['socket']:
            conections[conn]['socket'].send(mesaj.encode(FORMAT))


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    print("Socket conectat la portul", PORT)
    server.listen()
    print("Socketul asculta")

    while True:
        # stabilim o conexiune cu un client
        conexion, address = server.accept()
        # activare thread client
        thread = threading.Thread(
            target=handle_client, args=(conexion, address))
        thread.start()
        print('Numarul de conexiuni curente: ' +
              str(threading.activeCount() - 1))
    s.close()


if __name__ == "__main__":
    main()
