import json
from typing import Dict, Tuple, List
from ast import literal_eval as make_tuple
from time import mktime, strptime, sleep, time
import sys
from math import floor

sendThis: Dict[Tuple[str, str, str], Tuple[str, bool]] = {
    ('Tester1', 'Potato', 'Sat Apr 11 22:10:30 2020'): (
        'Hey', True),
    ('Tester1', 'Potato', 'Sat Apr 11 22:10:45 2020'): (
        'Hey HEy', True),
    ('Tester2', 'Potato', 'Sat Apr 11 22:10:15 2020'): (
        'STOP THAT', True)
}


def prRed(skk, **kwargs): print("\033[91m{}\033[00m".format(skk), **kwargs)


def prGreen(skk, **kwargs): print("\033[92m{}\033[00m".format(skk), **kwargs)


def prYellow(skk, **kwargs): print("\033[93m{}\033[00m".format(skk), **kwargs)


def prLightPurple(skk, **kwargs): print("\033[94m{}\033[00m".format(skk), **kwargs)


def prPurple(skk, **kwargs): print("\033[95m{}\033[00m".format(skk), **kwargs)


def prCyan(skk, **kwargs): print("\033[96m{}\033[00m".format(skk), **kwargs)


def prLightGray(skk, **kwargs): print("\033[97m{}\033[00m".format(skk), **kwargs)


def prBlack(skk, **kwargs): print("\033[98m{}\033[00m".format(skk), **kwargs)


def dumper(info: Dict[Tuple[str, str, str], Tuple[str, bool]]) -> str:
    new: Dict[str, Tuple[str, bool]] = {}
    for key in info:
        new[str(key)] = info[key]
    return json.dumps(new)


def loader(info: str) -> Dict[Tuple[str, str, str], Tuple[str, bool]]:
    infDict = json.loads(info)
    new: Dict[Tuple[str, str, str], Tuple[str, bool]] = {}
    for key in infDict:
        new[make_tuple(key)] = tuple(infDict[key])
    return new


def potato(n: int = 1) -> str:
    return "\U0001f954" * n


def sorter(msg: Dict[Tuple[str, str, str], Tuple[str, bool]]):
    info = list(msg.items())
    info.sort(key=lambda it: mktime(strptime(it[0][2])))
    return info


def downloadProg(done: int, total: int, prevChr: int, length: int, startTime: float, fillChr: str = potato(),
                 remChr: str = '🤞'):
    if prevChr != 0:
        sys.stdout.write('\r' * prevChr)
    percent = floor(done * 100 / total)
    chrLen = floor(percent * length / 100)
    if time() - startTime > 0.00001:

        speed = (done / (time() - startTime)) / (1024 * 1000)
    else:
        speed = 0
    bar = f'[{(fillChr * chrLen).ljust(length, remChr)}] {percent}% @{speed}MB/sec'
    mainBar = "\033[93m{}\033[00m".format(bar)
    sys.stdout.write(mainBar)
    return len(mainBar)

# prYellow('Download:')
# prev = downloadProg(0, 100, 0, 50)
# for i in range(100):
#     sleep(0.01)
#     prev = downloadProg(i + 1, 100, prev, 50)
# print('Hey')
