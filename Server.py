import socket
import sys
import os
from time import ctime, mktime, strptime, time
import Formatting as Fm
from typing import Dict, Tuple, List
import threading
from platform import system
from copy import deepcopy
from pathlib import Path
import json
from hashlib import blake2b

# This if statement is for enabling colored statements in terminal and python console.
if "win" in system().lower():  # works for Win7, 8, 10 ...
    from ctypes import windll

    k = windll.kernel32
    k.SetConsoleMode(k.GetStdHandle(-11), 7)

hdrStrLen = 64
hdrbyteSize = 64

rgConnected = True
myIP = socket.gethostbyname(socket.gethostname())
registrationServerIP = socket.gethostbyname(socket.gethostname())
port = 1234
queueLength = 5
enc = 'utf-8'
bufferSize = 64
uniChrSz = 1
timeOut = 60  # in Seconds
readChunkSize = 1024 * 128
writeChunkSize = 1024 * 128

# Message Dictionary
# * implies msg to all
# key tuple consists of sender's alias, reciever's alias and time sent
# value tuple consists of msg and bool for if it is read.
msg: Dict[Tuple[str, str, str], Tuple[str, bool]] = {
    ('admin', '*', 'Sat Apr 11 22:10:30 2020'): ('Welcome to Potato Messenger', True),
    ('Potato', 'Tomato', 'Sat Apr 11 22:10:30 2020'): ('How you doin\'?', False)
}

# Users Database
# Contains users and blake2b hashed passwords.
users: Dict[str, bytes] = {
    "admin": b"\x87g[\xa38\xb1\x1c\xb7\x83\xc7\xb6\xbf\xc2r@\xa6\x1f\x0c\xc4\xaa~\xe80Z'\x96\x89\x8e\x8f\x8f\xae\xd8"
             b"\x8en d\x93\x00\\\xe9V\xb7\xd2\\\xb0\xcf\xc8Y\x1dL\xb4\x0e\xac\xd3O\x0b\xe8*\xdfnlc\x16\xd8"}

registrationKeyHashed = b"\x08z'uJ3\xc7 \xb6\x0b\x9b\xc5\xc7\xa9\xc50\xd3Tl\xa2\xba\xac\xcd\x07\xcf\xd4\xea\xf2\x87" \
                        b"\x08L8e" \
                        b"\x8e\xbd\xca1\xd6\xa4\x92(\xbb*6(\x82\xc1\x10\xea\x01#I\xc9\xf5+\x8a+\x88\xaf\x10\xd4\xf5" \
                        b"\xd8\xdc "


def registrationHandler(reg: socket.socket, address):
    global rgConnected
    global sOpen
    global users
    keySize = int(reg.recv(hdrbyteSize).decode(enc).strip())
    hashKey = blake2b()
    rgConnected = True
    for _ in range(keySize):
        hashKey.update(reg.recv(1))
    if hashKey != registrationKeyHashed:
        reg.send("F".encode(enc))
        rgConnected = False
        return
    reg.send("S".encode(enc))

    try:
        while 1:
            updateSize = int(reg.recv(hdrbyteSize).decode(enc).strip())
            updateJSON = ""
            for _ in range(updateSize):
                updateJSON += reg.recv(1).decode(enc)
            update = json.loads(updateJSON)
            users.update(update)
    except Exception as error:
        Fm.prRed(f'{lgSt("DISCONNECT")} {address} was disconnected due to an error. {error}')
        reg.close()


# Drive Info Dictionary.
# * implies all have access.
# Key is a path to a specific file in drive
# Value is a tuple of authorized users and time last modified.
driveInf: Dict[Path, Tuple[List[str], str]] = {
    Path('Drive/admin/Welcome.txt'): (['*'], 'Fri Apr 17 22:16:37 2020'),
    Path('Drive/admin/download.jpg'): (['*'], 'Fri Apr 17 22:16:37 2020'),
    Path('Drive/admin/100MB.bin'): (['*'], 'Fri Apr 17 22:16:37 2020')
}
sOpen = False


def lgSt(state: str = None) -> str: return f'[{ctime()}][{state}]' if state is not None else f'[{ctime()}][LOG]'


def updateTypeChecker(updateDict: Dict):
    if not isinstance(updateDict, dict):
        return False
    for key, value in updateDict.items():
        if not (isinstance(key, tuple) and isinstance(value, tuple)):
            return False
        if not any(isinstance(i, str) for i in key):
            return False
        if not isinstance(value[0], str):
            return False
        if not isinstance(value[1], bool):
            return False
    return True


def letUpdateTypeCheck(up: object) -> bool:
    if not isinstance(up, dict):
        return False
    for key, value in up.items():
        if not isinstance(key, str):
            return False
        if not isinstance(value, str):
            return False
    return True


def getClientFiles(al: str) -> List[str]:
    clFiles: List[str] = []
    for key in driveInf:
        if al in driveInf[key][0] or '*' in driveInf[key][0]:
            clFiles.append(str(key))
    return clFiles


def updateValidityChecker(updateDict: Dict[Tuple[str, str, str], Tuple[str, bool]],
                          mainMsg: Dict[Tuple[str, str, str], Tuple[str, bool]], alias: str) -> Tuple[
    bool, Dict[Tuple[str, str, str], Tuple[str, bool]]]:
    deleteThis: List[Tuple[str, str, str]] = []
    changeTime: List[Tuple[str, str, str]] = []
    for key, value in updateDict.items():
        if key[0] != alias:
            return False, updateDict
        sentTime = mktime(strptime(key[2]))
        if sentTime > time() or key in mainMsg:
            changeTime.append(key)
        if value[1]:
            updateDict[key] = value[0], False

    for key in changeTime:
        deleteThis.append(key)
        updateDict[(key[0], key[1], ctime())] = updateDict[key]

    for key in deleteThis:
        del updateDict[key]

    return True, updateDict


def getClientView(alias: str):
    view: Dict[Tuple[str, str, str], Tuple[str, bool]] = {}
    for key, value in msg.items():
        if key[1] == alias or key[1] == '*' or key[0] == alias:
            view[key] = value
    return view


def setRead(al):
    global msg
    copyMsg = deepcopy(msg)
    for key in copyMsg:
        if key[1] == al:
            msg[key] = msg[key][0], True


def handleConnection(client: socket.socket, address):
    global msg
    global sOpen
    global driveInf
    # get alias header.
    try:
        aliasSize = int(client.recv(hdrbyteSize).decode(enc).strip())
        alias = ''
        lastActive = time()
        for _ in range(aliasSize):
            alias += client.recv(1).decode(enc)
        passwordSize = int(client.recv(hdrbyteSize).decode(enc).strip())
        passwordHash = blake2b()
        lastActive = time()
        for _ in range(passwordSize):
            passwordHash.update(client.recv(1))
        if users[alias] != passwordHash.digest():
            client.send("F".encode(enc))
            client.close()
            return
        client.send("S".encode(enc))

        Fm.prCyan(f'{lgSt("CONNECTION")} {alias} connected to the server')
        # Receive loop.
        done = False
        while not done:
            if not sOpen:
                return
            req = client.recv(uniChrSz).decode(enc)
            if req == 'r':
                lastActive = time()
                setRead(alias)
                clView = getClientView(alias)
                clViewJson = Fm.dumper(clView)
                mainResp = clViewJson.encode(enc)
                jsonSize = len(mainResp)
                hdrRsp = str(jsonSize).ljust(hdrStrLen, ' ')
                client.send(hdrRsp.encode(enc))
                client.send(mainResp)
            elif req == 's':
                lastActive = time()
                sze = int(client.recv(hdrbyteSize).decode(enc).strip())
                clientUpdate = ''
                for _ in range(sze):
                    clientUpdate += client.recv(1).decode(enc)
                newData = Fm.loader(clientUpdate)
                if updateTypeChecker(newData):
                    valid, newData = updateValidityChecker(newData, msg, alias)
                    if not valid:
                        newData = {}
                        client.send('F'.encode(enc))
                    else:
                        client.send('S'.encode(enc))
                else:
                    newData = {}
                    client.send('F'.encode(enc))
                msg.update(newData)
                if newData:
                    msgRcv = [i[1] if i[1] != '*' else 'Everyone' for i in newData]
                    Fm.prCyan(
                        f'{lgSt()} {alias} sent {"a message" if len(msgRcv) == 1 else "messages"} to {", ".join(msgRcv[:-1])}{", and " if msgRcv[:-1] else ""}{msgRcv[-1]}.')
            elif req == 'u':
                lastActive = time()
                sze = int(client.recv(hdrbyteSize).decode(enc).strip())
                fileName = ''
                for _ in range(sze):
                    fileName += client.recv(1).decode(enc)
                if not os.path.exists(str(Path('Drive', alias))):
                    os.makedirs(str(Path('Drive', alias)))
                fileSze = int(client.recv(hdrbyteSize).decode(enc).strip())
                filePath = Path('Drive', alias, fileName)
                with open(str(filePath), 'wb') as File:
                    cnt = 0
                    while cnt < fileSze:
                        chunk = client.recv(writeChunkSize)
                        File.write(chunk)
                        cnt += len(chunk)
                driveInf[filePath] = ([alias], ctime())
                client.send('S'.encode(enc))
                Fm.prCyan(f'{lgSt()} {alias} uploaded {str(filePath.name)} to {str(filePath.stem)}.')
            elif req == 'd':
                lastActive = time()
                clFiles = json.dumps(getClientFiles(alias))
                clFileByte = clFiles.encode(enc)
                clFileSz = str(len(clFileByte)).ljust(hdrStrLen, ' ').encode(enc)
                client.send(clFileSz)
                client.send(clFileByte)
            elif req == 'l':
                lastActive = time()
                sz = int(client.recv(hdrbyteSize).decode(enc).strip())
                upDictJSON = ''
                for _ in range(sz):
                    upDictJSON += client.recv(1).decode(enc)
                upDict = json.loads(upDictJSON)
                if letUpdateTypeCheck(upDict):
                    for f in upDict:
                        driveInf[Path(upDict[f])][0].append(f)
                    client.send('S'.encode(enc))
                else:
                    client.send('F'.encode(enc))
            elif req == 'g':
                lastActive = time()
                pthSz = int(client.recv(hdrbyteSize).decode(enc).strip())
                filePath = ''
                for _ in range(pthSz):
                    filePath += client.recv(1).decode(enc)
                if filePath in getClientFiles(alias):
                    client.send('S'.encode(enc))
                    fPath = Path(filePath)
                    if fPath.exists():
                        client.send('Y'.encode(enc))
                        fileSize = fPath.stat().st_size
                        fileSizeHdr = str(fileSize).ljust(hdrStrLen).encode(enc)
                        client.send(fileSizeHdr)
                        with open(filePath, 'rb') as driveFile:
                            byte = driveFile.read(readChunkSize)
                            client.send(byte)
                            while byte:
                                byte = driveFile.read(readChunkSize)
                                client.send(byte)
                        user = client.recv(uniChrSz).decode()
                        Fm.prCyan(f'{lgSt()} {alias} downloaded {filePath}')
                    else:
                        client.send('N'.encode(enc))
                else:
                    client.send('F'.encode(enc))
            elif req == 'q':
                lastActive = time()
                client.close()
                Fm.prCyan(f'{lgSt("DISCONNECT")} {alias} disconnected from the server.')
                done = True
            else:
                if time() - lastActive > timeOut:
                    client.close()
                    Fm.prCyan(f'{lgSt("DISCONNECT")} {alias} was kicked out due to inactivity.')
                    done = True
    except Exception as error:
        Fm.prRed(f'{lgSt("DISCONNECT")} {address} was disconnected due to an error. {error}')
        client.close()


# Socket Creation
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
        s.bind((myIP, port))
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


def threadMaker(s: socket.socket):
    global sOpen
    handlers: List[threading.Thread] = []
    try:
        while True:
            if sOpen:
                client, address = s.accept()
                if not rgConnected and address[0] == registrationServerIP:
                    rgHandlerThread = threading.Thread(target=lambda: registrationHandler(client, address))
                    handlers.append(rgHandlerThread)
                    rgHandlerThread.start()
                else:
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


def handleMaker(client: socket.socket, address: Tuple):
    def handler():
        return handleConnection(client, address)

    return handler


if __name__ == '__main__':
    main()
