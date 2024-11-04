import subprocess
import re
import datetime

_verbose = False


def set_verbosity(verbosity: bool):
    global _verbose
    _verbose = verbosity


def verbose() -> bool:
    global _verbose
    return _verbose


def capture(cmd):
    if _verbose:
        print(cmd)
    result = subprocess.run(
        cmd,
        shell=True,
        executable="/usr/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return result.stdout.decode('utf-8')


def parse_storage(storage: str) -> float:
    if storage == '0':
        return 0

    num, postfix = float(storage[:-1]), storage[-1]
    if postfix == 'K':
        return num/1e6
    elif postfix == 'M':
        return num/1e3
    elif postfix == 'G':
        return num
    elif postfix == 'T':
        return num*1e3


# Parses a date string in the format 2023-01-01 to a datetime object
def parse_date(date: str) -> datetime:
    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    date = remove_day(date)
    return date


def remove_day(date) -> datetime:
    if isinstance(date, str):
        date = parse_date(date)
    date = date.replace(day=1)
    return date


# Converts elapsed time returned by sacct to hours
def parse_time(time: str) -> int:
    if '-' in time:
        ind = time.index('-')
        days = int(time[0:ind])
        return 24*days + parse_time(time[ind+1:])

    hrs, mins, secs = [int(i) for i in time.split(':')]

    return secs/3600 + mins/60 + hrs


mem_pattern = re.compile(r'([0-9.]+)([a-zA-Z]+)')


# Parses memory output of sacct to produce the gigabytes used
def parse_mem(mem: str, ncores: int, nodes: int) -> int:
    matches = mem_pattern.match(mem)
    num = matches.group(1)
    info = matches.group(2)

    if float(num) == 0.0:
        return 0.0

    if info[0] == 'G':
        gigabytes = float(mem[:-2])
    elif info[0] == 'M':
        gigabytes = float(mem[:-2])/1000
    else:
        raise ValueError

    if info[1] == 'n':
        gigabytes *= int(nodes)
    elif info[1] == 'c':
        gigabytes *= int(ncores)

    return gigabytes


# Converts elapsed time and number of cpus to CPU hours
def get_usage_time(elapsed: str, ncpu: str) -> int:
    time = parse_time(elapsed)
    return time*int(ncpu)


