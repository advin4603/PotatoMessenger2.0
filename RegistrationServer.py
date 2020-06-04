import socket
from hashlib import blake2b
from typing import List, Tuple
import threading
import Formatting as Fm
from time import ctime
from platform import system
import sys
import re
import json

# This block of code is for enabling colored statements in terminal and python console.
if "win" in system().lower():  # works for Win7, 8, 10 ...
    from ctypes import windll

    k = windll.kernel32
    k.SetConsoleMode(k.GetStdHandle(-11), 7)

hdrStrLen = 64
hdrbyteSize = 64

ServerIP = socket.gethostbyname(socket.gethostname())
myIP = socket.gethostbyname(socket.gethostname())
port = 1234
queueLength = 5
enc = 'utf-8'
bufferSize = 64
uniChrSz = 1
timeOut = 60  # in Seconds
updates = []
key = b'\xa6-\x03`p5\x0er\x06Nd\xeff\x03\x82Z\x12,' \
      b'\x15c\xec\r\x08\xd1\rqI\xa0\xcd\x88\x90\x15\xa0\xbc\xbd\x98\x03\\\xd8el\x02\r\no\xe5Ns\x00\xa1\x89u\xc9\xc0mn' \
      b'\x1f\xe2\xeaJ\x8d\x8e\xc3b '


def lgSt(state: str = None) -> str: return f'[{ctime()}][{state}]' if state is not None else f'[{ctime()}][LOG]'


def handleConnection(client: socket.socket, address):
    global updates
    try:
        aliasSize = int(client.recv(hdrbyteSize).decode(enc).strip())
        alias = ''
        for _ in range(aliasSize):
            alias += client.recv(1).decode(enc)
        passwordSize = int(client.recv(hdrbyteSize).decode(enc).strip())
        password = ''
        for _ in range(passwordSize):
            password += client.recv(1).decode(enc)
        if len(password) < 8:
            flag = 1
        elif not re.search("[a-z]", password):
            flag = 2
        elif not re.search("[A-Z]", password):
            flag = 3
        elif not re.search("[0-9]", password):
            flag = 4
        elif not re.search("[_@$]", password):
            flag = 5
        else:
            flag = 0
        client.send(str(flag).encode(enc))
        if flag == 0:
            passwordHash = blake2b()
            passwordHash.update(password.encode(enc))
            updates.append((alias.encode(enc), passwordHash.digest()))


    except Exception as error:
        Fm.prRed(f'{lgSt("DISCONNECT")} {address} was disconnected due to an error. {error}')
        client.close()


def updateSender():
    global updates
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((ServerIP, port))
    server.send(str(len(key)).ljust(hdrStrLen).encode(enc))
    server.send(key)
    success = server.recv(1).decode(enc)
    if success == "F":
        raise Exception("You are not Authorized!!")
    while True:
        if updates:
            updateJson = json.dumps({item[0]: item[1] for item in updates}).encode(enc)
            updates.clear()
            updateSize = str(len(updateJson)).ljust(hdrStrLen).encode(enc)
            server.send(updateSize)
            server.send(updateJson)

def handleMaker(client: socket.socket, address: Tuple):
    def handler():
        return handleConnection(client, address)

    return handler


def threadMaker(s: socket.socket):
    global sOpen
    handlers: List[threading.Thread] = []
    serverHandlerThread = threading.Thread(target=updateSender)
    handlers.append(serverHandlerThread)
    serverHandlerThread.start()
    try:
        while True:
            if sOpen:
                client, address = s.accept()
                sktHandler = handleMaker(client, address)
                handleThread = threading.Thread(target=sktHandler)
                handlers.append(handleThread)
                handleThread.start()
            else:
                break
    except OSError:
        pass
    finally:
        if sOpen:
            s.close()
        sOpen = False
        Fm.prGreen(f'{lgSt("QUIT")} Successfully closed socket.')


def main():
    global sOpen
    try:
        Fm.prCyan(f'{lgSt("INITIALIZING")} Creating socket.')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sOpen = True
    except BaseException as exc:
        Fm.prRed(f'{lgSt("ERROR")} {exc}')
        Fm.prYellow(f'{lgSt()} Socket could not be created.')
        Fm.prYellow(f'{lgSt("QUIT")} Quitting now')
        sOpen = False
        sys.exit()

    Fm.prGreen(f'{lgSt()} Successfully created Socket.')

    # Binding socket to given ip at given port
    try:
        Fm.prCyan(f'{lgSt("BINDING")} Binding socket to {myIP} at {port}')
        # TODO Use Different Port for Registration and Main Server
        s.bind((myIP, port+1))
    except BaseException as exc:
        Fm.prRed(f'{lgSt("ERROR")} {exc}')
        Fm.prYellow(f'{lgSt()} Socket could not be bound to {myIP} at {port}')
        s.close()
        Fm.prGreen(f'{lgSt("QUIT")} Successfully closed socket.')
        Fm.prYellow(f'{lgSt("QUIT")} Quitting now')
        sOpen = False
        sys.exit()

    Fm.prGreen(f'{lgSt()} Successfully binded Socket to {myIP} at {port}.')

    # Listening to Connections

    s.listen(queueLength)
    Fm.prCyan(f'{lgSt()} Listening for connections at {port} on {myIP}')
    makeThread = threading.Thread(target=threadMaker, args=(s,))
    makeThread.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        if sOpen:
            s.close()
        sOpen = False
