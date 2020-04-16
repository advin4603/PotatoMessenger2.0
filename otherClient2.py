import socket
import threading
from time import ctime
from typing import List, Tuple, Dict
import sys
import Formatting as Fm
import traceback
from platform import system
import os

# This if statement is for enabling colored statements in terminal and python console.
if "win" in system().lower():  # works for Win7, 8, 10 ...
    from ctypes import windll

    k = windll.kernel32
    k.SetConsoleMode(k.GetStdHandle(-11), 7)
# sendThis: List[Dict[Tuple[str, str, str], Tuple[str, bool]]] = [
#     {
#         ('Tester1', 'Potato', 'Sat Apr 11 22:10:30 2020'): (
#             'Hey', True)
#     }
# ]
sendThis: List[Dict[Tuple[str, str, str], Tuple[str, bool]]] = []
# Message Dictionary
# * implies msg to all
# key tuple consists of sender's alias, reciever's alias and time sent
# value tuple consists of msg and bool for if it is read.
myMsg: Dict[Tuple[str, str, str], Tuple[str, bool]] = {}
done = False
status: List[str] = []
# Change these sizes if using other encoding.
hdrStrLen = 64
hdrbyteSize = 64

myIP = socket.gethostbyname(socket.gethostname())
port = 1234
queueLength = 5
enc = 'utf-8'
bufferSize = 64
uniChrSz = 1
timeOut = 60  # in Seconds


def handleServer(server: socket.socket):
    global myMsg
    global sendThis
    global status
    global done
    try:
        while not done:
            if sendThis:
                req = 's'.encode(enc)
                server.send(req)
                a = sendThis.pop(-1)
                sendMsg = Fm.dumper(a).encode(enc)
                sz = len(sendMsg)
                header = str(sz).ljust(hdrStrLen).encode(enc)
                server.send(header)
                server.send(sendMsg)
                st = server.recv(uniChrSz).decode(enc)
                status.append(st)
            else:
                req = 'r'.encode(enc)
                server.send(req)
                sz = int(server.recv(hdrbyteSize).decode(enc).strip())
                newJson = bytes('', 'utf-8')
                for _ in range(sz):
                    newJson += server.recv(1)
                newMsg = Fm.loader(newJson.decode(enc))
                myMsg.update(newMsg)

        else:
            req = 'q'.encode(enc)
            server.send(req)
    except ConnectionError:
        Fm.prRed('The Server closed the connection.')
        Fm.prCyan('Quitting...')

    finally:
        server.close()
        os._exit(0)


def viewPrinter(myMsg, alias: str):
    sortedView = Fm.sorter(myMsg)
    for msg in sortedView:
        if msg[0][0] == alias:
            Fm.prYellow('-' * 100)
            rec = msg[0][1] if msg[0][1] != '*' else 'Everyone'
            to = f'To {rec}'.rjust(100, ' ')
            Fm.prGreen(to)
            on = f'On {msg[0][2]}'.rjust(100, ' ')
            Fm.prPurple(on)
            print()
            ms = '\n'.join([i.rjust(100, ' ') for i in msg[1][0].split('\n')])
            Fm.prCyan(ms)
            if msg[0][1] != '*':
                print()
                if msg[1][1]:
                    Fm.prPurple(f'Read by {msg[0][1]}'.rjust(100, ' '))
                else:
                    Fm.prPurple(f'Not read by {msg[0][1]}'.rjust(100, ' '))
            Fm.prYellow('-' * 100)
        else:
            Fm.prBlack('-' * 100)
            sender = msg[0][0]
            by = f'From {sender}'
            Fm.prCyan(by)
            on = f'On {msg[0][2]}'
            Fm.prGreen(on)
            print()
            Fm.prPurple(msg[1][0])
            Fm.prBlack('-' * 100)


def handleClient():
    global done
    global status
    intro = 'Potato Messenger 2.0'
    Fm.prYellow(intro.center(len(intro) + 4, " ").center(len(intro) + 91, Fm.potato()))
    print('\n' * 2)
    Fm.prPurple('Login as\n>', end='')
    alias = input('')
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((socket.gethostbyname(socket.gethostname()), 1234))
    except:
        with open('Traceback.txt', 'w') as f:
            Fm.prRed('Some unknown error occurred while connecting to server. View traceback.txt for details.')
            print(traceback.format_exc(), file=f)
        sys.exit()

    aliasByte = bytes(alias, enc)
    aliasSz = len(aliasByte)
    aliasHeader = bytes(str(aliasSz).ljust(hdrStrLen), enc)
    server.send(aliasHeader)
    server.send(aliasByte)
    Fm.prGreen(f'Successfully Logged in as {alias}')
    handler = threading.Thread(target=lambda: handleServer(server))
    handler.start()
    while not done:
        Fm.prLightPurple("""Commands:
        s->Send a msg
        r->Read your inbox
        r X->Read all messages between you and X.(X stands for another user's username)
        q->Quit""")
        Fm.prPurple('>', end='')
        user = input()
        if user.lower() == 'q':
            Fm.prCyan('Quitting...')
            done = True
        elif user.lower() == 'r':
            print('\n' * 1000)
            Fm.prYellow(intro.center(len(intro) + 4, " ").center(len(intro) + 91, Fm.potato()))
            print('\n' * 2)
            viewPrinter(myMsg, alias)
        elif user.lower()[:2] == 'r ':
            otherAlias = user[2:]
            specificView: Dict[Tuple[str, str, str], Tuple[str, bool]] = {}
            for ms in myMsg:
                if ms[0] == otherAlias or ms[1] == otherAlias:
                    specificView[ms] = myMsg[ms]
            print('\n' * 1000)
            Fm.prYellow(intro.center(len(intro) + 4, " ").center(len(intro) + 91, Fm.potato()))
            print('\n' * 2)
            if specificView:
                viewPrinter(specificView, alias)
            Fm.prYellow('Wow, Such empty.'.center(100, ' '))
        elif user.lower() == 's':
            print('\n' * 2)
            Fm.prPurple('Enter Recipient 1(Enter * to send msg to everyone using Potato Messenger)\n>', end='')
            r = [input()]
            while r[0] == '':
                print()
                Fm.prPurple('Enter Recipient 1\n>', end='')
                r = [input()]
            i = 2
            if r[0] != '*':
                while True:
                    Fm.prPurple(f'Enter Recipient {i}(To continue press enter without typing anything)\n>', end='')
                    rec = input()
                    if rec == '':
                        break
                    else:
                        r.append(rec)
                        i += 1
            print('\n')
            Fm.prCyan('''Type your message
            1)For new line press Enter and type your message.
            2)To submit press Enter twice.
            3)For an empty line press Enter to create a new line then enter a space then again press Enter. ''')
            lines = []
            while True:
                Fm.prPurple('>', end='')
                ln = input()
                if ln == '':
                    break
                lines.append(ln)
            msg = '\n'.join(lines)
            send: Dict[Tuple[str, str, str], Tuple[str, bool]] = {}
            if '*' in r:
                key = (alias, '*', ctime())
                send[key] = (msg, True)
                recipients = 'Everyone using Potato Messenger.'
            else:
                for reci in r:
                    key = (alias, reci, ctime())
                    send[key] = (msg, False)
                recipients = ', '.join(r[:-1]) + f', and {r[-1]}' if len(r) != 1 else r[0]
            while True:
                print()
                Fm.prYellow(f'Confirm message to {recipients}(Yes or No)\n>', end='')
                ch = input()
                if ch.lower() in ['yes', 'y', 'yeah', 'yup']:
                    sendThis.append(send)
                    print()
                    Fm.prYellow('Sending...')
                    while not status:
                        pass
                    else:
                        if status.pop(-1):
                            Fm.prGreen('Message Sent Successfully.')
                            break
                        else:
                            Fm.prRed('Message not sent..')
                            repeat = True
                            while repeat:
                                Fm.prYellow('Send Again(Yes or No)\n>', end='')
                                again = input()
                                if again.lower() in ['yes', 'y', 'yeah', 'yup']:
                                    break
                                elif again.lower() in ['no', 'n', 'nope', 'nah']:
                                    repeat = False
                                else:
                                    Fm.prRed("I didn't understand that.")
                                    print()
                            else:
                                break
                elif ch.lower() in ['no', 'n', 'nope', 'nah']:
                    break
                else:
                    Fm.prRed("I didn't understand that.")
        else:
            print('\n' * 1000)
            Fm.prYellow(intro.center(len(intro) + 4, " ").center(len(intro) + 91, Fm.potato()))
            print('\n' * 2)

            Fm.prYellow(f'{user} is not a valid command.')


handleClient()
Fm.prGreen('Successfully quit.')
