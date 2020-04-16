import socket
import sys
from time import ctime, mktime, strptime, time
import Formatting as Fm
from typing import Dict, Tuple, List
import threading
from platform import system

# This if statement is for enabling colored statements in terminal and python console.
if "win" in system().lower():  # works for Win7, 8, 10 ...
    from ctypes import windll

    k = windll.kernel32
    k.SetConsoleMode(k.GetStdHandle(-11), 7)

hdrStrLen = 64
hdrbyteSize = 64

myIP = socket.gethostbyname(socket.gethostname())
port = 1234
queueLength = 5
enc = 'utf-8'
bufferSize = 64
uniChrSz = 1
timeOut = 60  # in Seconds

# Message Dictionary
# * implies msg to all
# key tuple consists of sender's alias, reciever's alias and time sent
# value tuple consists of msg and bool for if it is read.
msg: Dict[Tuple[str, str, str], Tuple[str, bool]] = {
    ('admin', '*', 'Sat Apr 11 22:10:30 2020'): ('Welcome to Potato Messenger', True),
    ('Potato', 'Tomato', 'Sat Apr 11 22:10:30 2020'): ('How you doin\'?', False)
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


def handleConnection(client: socket.socket, address):
    global msg
    global sOpen
    # get alias header.
    try:
        aliasSize = int(client.recv(hdrbyteSize).decode(enc).strip())
        alias = ''
        lastActive = time()
        for _ in range(aliasSize):
            alias += client.recv(1).decode(enc)
        Fm.prCyan(f'{lgSt("CONNECTION")} {alias} connected to the server')
        # Receive loop.
        done = False
        while not done:
            if not sOpen:
                return
            req = client.recv(uniChrSz).decode(enc)
            if req == 'r':
                lastActive = time()
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