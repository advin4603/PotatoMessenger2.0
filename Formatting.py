import json
from typing import Dict, Tuple, List
from ast import literal_eval as make_tuple
from time import mktime,strptime

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
    info.sort(key=lambda it:mktime(strptime(it[0][2])))
    return info



