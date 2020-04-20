import socket
import threading
from time import ctime, time
from typing import List, Tuple, Dict
import sys
import Formatting as Fm
import traceback
from platform import system
import os
import json
from pathlib import Path

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
myFiles: List[str] = []
giveAccess: List[Dict[str, str]] = []
getDriveInf: bool = False
DriveInf: List[str] = []
downloadThis: List[str] = []
downloading: bool = True
uploadThis: List[Path] = []
uploading: bool = False
posResp = ['yes', 'y', 'yeah', 'yup']
negResp = ['no', 'n', 'nope', 'nah']
shareThis:List[Dict[str,Path]] = []
sharing = True
# Message Dictionary
# * implies msg to all
# key tuple consists of sender's alias, receiver's alias and time sent
# value tuple consists of msg and bool for if it is read.
myMsg: Dict[Tuple[str, str, str], Tuple[str, bool]] = {}
done = False
status: List[bool] = []
# Change these sizes if using other encoding.
hdrStrLen = 64
hdrbyteSize = 64
writeChunkSize = 1024 * 128
readChunkSize = 1024 * 128

ServerIP = socket.gethostbyname(socket.gethostname())
port = 1234
queueLength = 5
enc = 'utf-8'
bufferSize = 64
uniChrSz = 1
timeOut = 60  # in Seconds


def FilePrinter(dInf: List[str]):
    w1 = 11
    w2 = 40
    w3 = 80
    pad = '-'
    header = '||' + 'S.No.'.center(w1, pad) + '|' + 'FileName'.center(w2, pad) + '|' + 'FilePath'.center(80, pad) + '||'
    Fm.prLightPurple(header)
    for index, pth in enumerate(dInf):
        ptObj = Path(pth)
        row = '||' + str(index + 1).center(w1, pad) + '|' + str(ptObj.name).center(w2, pad) + '|' + str(ptObj).center(
            w3, pad) + '||'
        Fm.prCyan(row)


def handleServer(server: socket.socket):
    """Thread to Send Handle Server. Sending Requests,quit msgs,and receive and send requests"""
    global myMsg
    global sendThis
    global status
    global done
    global getDriveInf
    global DriveInf
    global downloading
    global downloadThis
    global uploading
    global uploadThis
    global shareThis
    global sharing
    try:
        while not done:
            # Check if user wants to send something by checking sendThis list.
            if sendThis:
                # Send 's' request to server
                req = 's'.encode(enc)
                server.send(req)

                # pop the msg from sendThis then dump it into a JSON Format.
                a = sendThis.pop(-1)
                sendMsg = Fm.dumper(a).encode(enc)

                # Send size of coming msg then send the msg
                sz = len(sendMsg)
                header = str(sz).ljust(hdrStrLen).encode(enc)
                server.send(header)
                server.send(sendMsg)

                # Receive whether message sent Successfully or not
                st = server.recv(uniChrSz).decode(enc)
                state = True if st == 'S' else False
                status.append(state)
            elif getDriveInf:
                req = 'd'.encode(enc)
                server.send(req)
                sz = int(server.recv(hdrbyteSize).decode(enc).strip())
                paths = ''
                for _ in range(sz):
                    paths += server.recv(1).decode(enc)
                DriveInf.clear()
                DriveInf.extend(json.loads(paths))
                getDriveInf = False
            elif sharing:
                if shareThis:
                    upd = shareThis.pop(-1)
                    updFormatted:Dict[str,str] = {}
                    for user in upd:
                        updFormatted[user] = str(upd[user])
                    server.send('l'.encode(enc))
                    share = json.dumps(updFormatted).encode(enc)
                    sz = str(len(share)).ljust(hdrStrLen).encode(enc)
                    server.send(sz)
                    server.send(share)
                    success = server.recv(uniChrSz).decode(enc)
                    print(success)
                    if success == 'S':
                        Fm.prGreen('Successfully shared files.')
                    else:
                        Fm.prRed('Sharing Failed!')
                else:
                    sharing = False
            elif uploading:
                if uploadThis:
                    req = 'u'.encode(enc)
                    server.send(req)

                    upPth = uploadThis.pop(0)
                    fName = upPth.name.encode(enc)
                    sze = str(len(fName)).ljust(hdrStrLen).encode(enc)
                    server.send(sze)
                    server.send(fName)
                    fileSize = upPth.stat().st_size
                    fileSizeHdr = str(fileSize).ljust(hdrStrLen).encode(enc)
                    server.send(fileSizeHdr)
                    Fm.prYellow(f'Uploading {fName}({fileSize} bytes):')
                    with open(str(upPth), 'rb') as driveFile:
                        byte = driveFile.read(readChunkSize)
                        server.send(byte)
                        start = time()
                        prev = Fm.downloadProg(0, fileSize, 0, 50, start)
                        cnt = 0
                        while byte:
                            byte = driveFile.read(readChunkSize)
                            server.send(byte)
                            cnt += len(byte)
                            prev = Fm.downloadProg(cnt, fileSize, prev, 50, start)
                        else:
                            _ = Fm.downloadProg(fileSize, fileSize, prev, 50, start)
                            print()

                    _ = server.recv(uniChrSz).decode()
                    Fm.prGreen(f'Successfully uploaded {fName}')
                    if not uploadThis:
                        uploading = False
                else:
                    uploading = False
            elif downloading:
                if downloadThis:
                    req = 'g'.encode(enc)
                    server.send(req)
                    pth = downloadThis.pop(-1)
                    pthByte = pth.encode(enc)
                    sz = str(len(pthByte)).ljust(hdrStrLen).encode(enc)
                    server.send(sz)
                    server.send(pthByte)
                    Fm.prYellow('Asking for access..')
                    access = server.recv(uniChrSz).decode(enc)
                    if access != 'S':
                        Fm.prRed(f'You don\'t have access to {pth}.\nDownload Failed!')
                        downloading = False
                        continue
                    Fm.prGreen('Access Granted!')
                    fileExists = server.recv(uniChrSz).decode(enc)
                    Fm.prYellow('Checking if file exists on the server.')
                    if fileExists != 'Y':
                        Fm.prRed(f'The file at {pth} does not exist.')
                        downloading = False
                        continue
                    Fm.prGreen('File found!')
                    Fm.prCyan('Starting Download..')
                    pthObj = Path(pth)
                    newPth = Path('Downloads', pthObj.name)
                    if not os.path.exists('Downloads'):
                        os.makedirs('Downloads')
                    else:
                        if newPth.exists():
                            Fm.prYellow('File already exists, Overwrite?(Yes or No)')
                            Fm.prPurple('>', end='')
                            overwrite = input()
                            print()
                            while True:
                                if overwrite.lower() in negResp:
                                    Fm.prPurple('Enter new file name(Without file extension)\n>', end='')
                                    newName = input()
                                    print()
                                    newPth = Path('Downloads', newName + newPth.suffix)
                                    break
                                elif overwrite.lower() in posResp:
                                    Fm.prLightPurple('Overwriting...')
                                    print()
                                    break
                                else:
                                    Fm.prRed('I didn\'t get that.')
                                    Fm.prYellow('File already exists, Overwrite?(Yes or No)')
                                    Fm.prPurple('>', end='')
                                    overwrite = input()
                                    print()
                    fileSz = int(server.recv(hdrbyteSize).decode(enc).strip())
                    Fm.prYellow(f'Downloading {fileSz} bytes:')
                    with open(newPth, 'wb') as file:
                        start = time()
                        prev = Fm.downloadProg(0, fileSz, 0, 50, start)
                        cnt = 0
                        while cnt < fileSz:
                            chunk = server.recv(writeChunkSize)
                            file.write(chunk)
                            cnt += len(chunk)
                            prev = Fm.downloadProg(cnt, fileSz, prev, 50, start)
                    print('\n')
                    server.send('D'.encode(enc))
                    Fm.prGreen(f'File Downloaded at {newPth}!')
                    downloading = False
                else:
                    downloading = False
            else:
                # If no messages to be sent then send read request to get latest messages.
                req = 'r'.encode(enc)
                server.send(req)

                # Get size of coming message
                sz = int(server.recv(hdrbyteSize).decode(enc).strip())

                # Receive the New message
                newJson = bytes('', 'utf-8')
                for _ in range(sz):
                    newJson += server.recv(1)
                newMsg = Fm.loader(newJson.decode(enc))

                # Update the current messages dict.
                myMsg.update(newMsg)

        else:
            # If done then send quit msg
            req = 'q'.encode(enc)
            server.send(req)
    except ConnectionError:
        Fm.prRed('The Server closed the connection.')
        Fm.prCyan('Quitting...')
    except BaseException:
        with open('Traceback.txt', 'w') as f:
            Fm.prRed('Some unknown error occurred during connection with server. View traceback.txt for details.')
            print(traceback.format_exc(), file=f)
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
    global getDriveInf
    global downloadThis
    global downloading
    global uploading
    global uploadThis
    global shareThis
    global sharing
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
        q->Quit
        drive->Get all files available for download.
        download X->Download the Xth file in your Drive(use drive to see file Serial numbers)
        upload X->Upload the file at location X to your drive. 
                  Right Click a file, then select properties where you can find the location.
                  Add fileName to the location.:LOCATION\\filename.extension
                  (Ex:F:\\Pycharm_projects\\PotatoMessenger2.0\\client.py)
        share X->Share the Xth file in your Drive(use drive to see file Serial numbers)
                  """)
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
            else:
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
                if ch.lower() in posResp:
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
                                if again.lower() in posResp:
                                    break
                                elif again.lower() in negResp:
                                    repeat = False
                                else:
                                    Fm.prRed("I didn't understand that.")
                                    print()
                            else:
                                break
                elif ch.lower() in negResp:
                    break
                else:
                    Fm.prRed("I didn't understand that.")
        elif user.lower() in 'drive':
            getDriveInf = True
            Fm.prYellow('Getting info...')
            while getDriveInf:
                pass
            FilePrinter(DriveInf)
        elif user.lower()[:7] == 'upload ':
            pth = Path(user[7:])
            if not pth.exists():
                Fm.prRed('The given path does not exist.')
                continue
            if pth.is_dir():
                Fm.prRed('You cannot upload a folder.(Try compressing it)')
                continue
            uploadThis.append(pth)
            uploading = True
            while uploading:
                pass
        elif user.lower()[:6] == 'share ':
            getDriveInf = True
            while getDriveInf:
                pass
            num = int(user.lower()[6:].strip())
            index = num - 1
            if not 0 <= index < len(DriveInf):
                Fm.prRed(f'There is no file with serial {num}.')
                continue
            while 1:
                share = Path(DriveInf[index])
                Fm.prYellow(f'Share {share.name}?')
                Fm.prPurple('>', end='')
                user = input()
                if user.lower() in posResp:
                    print('\n')
                    Fm.prPurple('Enter Recipient 1(Enter * to share file with everyone using Potato Messenger)\n>', end='')
                    r = [input()]
                    while r[0] == '':
                        print()
                        Fm.prPurple('Enter Recipient 1\n>', end='')
                        r = [input()]
                    i = 2
                    if r[0] != '*':
                        while True:
                            Fm.prPurple(f'Enter Recipient {i}(To continue press enter without typing anything)\n>',
                                        end='')
                            rec = input()
                            if rec == '':
                                break
                            else:
                                r.append(rec)
                                i += 1
                    if '*' in r:
                        shareReq:Dict[str,Path] = {'*':share}
                        recipients = 'Everyone using Potato Messenger.'
                    else:
                        shareReq:Dict[str,Path] = {}
                        for recipient in r:
                            shareReq[recipient] = share
                        recipients = ', '.join(r[:-1]) + f', and {r[-1]}' if len(r) != 1 else r[0]
                    Fm.prYellow(f'Confirm file share with {recipients}(Yes or No)\n>', end='')
                    while 1:
                        ch = input()
                        if ch.lower() in posResp:
                            shareThis.append(shareReq)
                            print()
                            Fm.prYellow('Sharing...')
                            sharing = True
                            while sharing:
                                pass
                            break
                        elif ch.lower() in negResp:
                            break
                        else:
                            Fm.prRed("I didn't understand that.")
                    break
                elif user.lower() in negResp:
                    break
                else:
                    Fm.prRed("I didn't understand that.")
        elif user.lower()[:9] == 'download ':
            getDriveInf = True
            while getDriveInf:
                pass
            num = int(user.lower()[9:].strip())
            index = num - 1
            if not 0 <= index < len(DriveInf):
                Fm.prRed(f'There is no file with serial {num}.')
                continue
            while True:
                Fm.prYellow(f'Download {Path(DriveInf[index]).name}?')
                Fm.prPurple('>', end='')
                user = input()
                if user.lower() in posResp:
                    print('\n')
                    downloadThis.append(DriveInf[index])
                    downloading = True
                    while downloading:
                        pass
                    break
                elif user.lower() in negResp:
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
