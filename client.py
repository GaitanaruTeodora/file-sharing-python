import socket
import threading
import sys

IP = "127.0.0.1"
PORT = 8095
FORMAT = "utf-8"
SIZE = 1024


user = {}  # datele despre clientul conectat
user_conectati = {}  # datele despre toti clientii conectati in afara de conexiunea actuala


def remove_users():
    while len(user_conectati) > 0:
        user_conectati.popitem()


def client_receive(client):
    global user_conectati
    while True:
        try:
            message_received = client.recv(1024).decode('utf-8')
            try:
                if 'APROB@' in message_received:

                    data = message_received.split("@")
                    print("Cerere aprobare CITIRE fisier")
                    r = input(
                        "APROBI Fisierul {} pentru userul {} (YES/NO) ? : ".format(data[3], data[1]))
                    if r.strip() == "YES":
                        send_data = f"RASPUNS@YES@{data[1]}@{data[2]}@{data[3]}"
                        client.send(send_data.encode(FORMAT))
                    else:
                        send_data = f"RASPUNS@NO@{data[1]}@{data[2]}@{data[3]}"
                        client.send(send_data.encode(FORMAT))
                elif 'CONTINUT@' in message_received:
                    data = message_received.split("@")

                    filepath = "user_data/downloads/" + data[1]
                    with open(filepath, "w") as f:
                        f.write(data[2])
                    print(
                        "Ai descarcat fisierul {} in folderul downloads".format(data[1]))

                elif 'DESCARC@' in message_received:
                    data = message_received.split("@")
                    print("Cerere aprobare DESCARCARE fisier")
                    r = input(
                        "APROBI Fisierul {} pentru userul {} (YES/NO) ? : ".format(data[3], data[1]))
                    if r.strip() == "YES":
                        send_data = f"RASPUNS-DESCARC@YES@{data[1]}@{data[2]}@{data[3]}"
                        client.send(send_data.encode(FORMAT))
                    else:
                        send_data = f"RASPUNS-DESCARC@NO@{data[1]}@{data[2]}@{data[3]}"
                        client.send(send_data.encode(FORMAT))

                elif "@" in message_received:
                    data = message_received.split("@")
                    remove_users()
                    for d in data:
                        if d != '':
                            rez = d.split(" ")
                            den = rez[0]
                            fisiere = rez[1].split("*")
                            fisiere = [x for x in fisiere if x != '']
                            if den != user[client]['username']:
                                user_conectati[den] = {
                                    "fisiere": fisiere
                                }
                            else:

                                user[client]["fisiere"] = fisiere

                    print("Lista a fost actualizata !")
                else:
                    print(message_received)

            except Exception as e:
                print(e)
                print("Mesaj primit de la server: \n", message_received)
        except:
            client.close()
            break


def main():
    global user
    global user_conectati
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP, PORT))
    print("S-a realizat conexiunea cu serverul pe portul ", PORT)

    condition = 1

    while True:
        condition = input("Choose option :Register(1)/Login(2): ")
        if condition == '1' or condition == '2':
            if condition == '1':
                print("\n############ Register ############  \n")
                username = input("Enter username : ")
               
                password = input('Enter password : ')
                if len(username) > 0 and len(password) > 0:
                    cmd = 'REGISTER'
                    send_data = f"{cmd}@{username}@{password}"
                    client.send(send_data.encode(FORMAT))
                    response = client.recv(SIZE).decode(FORMAT)
                    print(response)
                else:
                    print(
                        "Username sau parola trebuie sa contina cel putin un caracter.")

            else:
                print("\nLogin :\n")
                username = input("Enter username : ")
                password = input('Enter password : ')
                if len(username) > 0 and len(password) > 0:
                    cmd = 'LOGIN'
                    send_data = f"{cmd}@{username}@{password}"

                    client.send(send_data.encode(FORMAT))

                    response = client.recv(SIZE).decode(FORMAT)
                    info = response.split("@")

                    resp = info[0]
                    mess = info[1]
                    if resp == 'OK-LOGIN':
                        print(mess)
                        user[client] = {
                            "username": username,
                            "fisiere": []
                        }
                        break
                    else:
                        print(mess)
                else:
                    print(
                        "Username sau parola trebuie sa contina cel putin un caracter.")

        else:
            print("Comanda nu exista \n")

    thread = threading.Thread(target=client_receive, args=(client,))
    thread.start()
    print("####### {} esti conectat la sesiune ##### \n".format(
        user[client]['username']))
    print("#####################\n")
    print("Comenzi disponibile \n")
    print("1.LOGOUT \n")
    print("2.AFISEAZA \n")
    print("3.UPLOAD \n")
    print("4.DELETE \n")
    print("5.CITESTE \n")
    print("6.DESCARCA \n")
    while True:
        try:

            message = input("\n {}  >>  ".format(user[client]['username']))
           

            if message == "LOGOUT":
                client.send(message.encode('utf-8'))
                print('Logout ...')
                break
            if message == "DELETE":
                print("Alege fisierul pe care vrei sa-l stergi")

                for idx, fis in enumerate(user[client]['fisiere']):
                    print(str(idx+1)+"=> "+fis+'\n')
                rez = input("Denumire fisier ales : ")
                if rez not in user[client]['fisiere']:
                    print("Fisierul ales nu exista")
                else:
                    send_data = f"DELETE@{rez}"
                    client.send(send_data.encode(FORMAT))

            if message == "AFISEAZA":
                if len(user_conectati) == 0:
                    print("Esti singurul user conectat pe server")
                else:
                    for idx, user1 in enumerate(user_conectati):
                        if len(user_conectati[user1]['fisiere']) > 0 and user[client]['username'] != user1:
                            print("\n Username {} a incarcat : \n".format(user1))
                            for fiR in user_conectati[user1]['fisiere']:
                                print(str(idx+1)+" => "+fiR+"\n")
                        else:
                            print(
                                "\n Username {} nu are fisiere incarcate \n".format(user1))
            if message == 'CITESTE':
                print("\n Alege un user : \n")
                for us in user_conectati:
                    print("\n {} \n ".format(us))
                rasp = input("User ales : ")
                if rasp not in user_conectati:
                    print("\nUserul ales nu exista sau nu este conectat")
                else:
                    print("Alege fisierul pe care vrei sa-l citesti")
                    for fis in user_conectati[rasp]['fisiere']:
                        print("\n {} \n".format(fis))
                    sel = input("Fisier selectat: ")
                    if sel.strip() not in user_conectati[rasp]['fisiere']:
                        print("Fisierul selectat nu exista")
                    else:
                        print(
                            "Ai ales fisierul {} . Astept pentru aprobarea userului {}".format(sel, rasp))
                        send_data = f"APROB@{rasp}@{sel}"
                        client.send(send_data.encode(FORMAT))

            if message == 'DESCARCA':
                print("\n Alege un user : \n")
                for us in user_conectati:
                    print("\n {} \n ".format(us))
                rasp = input("User ales : ")
                if rasp not in user_conectati:
                    print("\nUserul ales nu exista sau nu este conectat")
                else:
                    print("Alege fisierul pe care vrei sa-l citesti")
                    for fis in user_conectati[rasp]['fisiere']:
                        print("\n {} \n".format(fis))
                    sel = input("Fisier selectat: ")
                    if sel.strip() not in user_conectati[rasp]['fisiere']:
                        print("Fisierul selectat nu exista")
                    else:
                        print(
                            "Ai ales fisierul {} . Astept pentru aprobarea userului {}".format(sel, rasp))
                        send_data = f"DESCARC@{rasp}@{sel}"
                        client.send(send_data.encode(FORMAT))

            if message == "UPLOAD":
                user_file = input(
                    "\n Alege fisierele (din folderul user_data): ")
                user_file = user_file.split(" ")
                send_data = "UPLOAD@"
                for path in user_file:
                    try:
                        path = 'user_data/'+path
                        text = ''
                        with open(f"{path}", "r") as f:
                            text = f.read()

                        filename = path.split("/")[-1]
                        data2 = f"${filename}*{text}$"
                        send_data = send_data + data2
                    except:
                        print("Fisierul {} nu exista \n ".format(path))

                client.send(send_data.encode(FORMAT))

        except KeyboardInterrupt:
            client.send("LOGOUT".encode('utf-8'))
            client.close()
            sys.exit()
    client.close()


if __name__ == "__main__":
    main()
