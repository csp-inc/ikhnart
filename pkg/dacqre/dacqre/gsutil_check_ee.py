import os
import subprocess
import datetime
from . import utils as ut


logfile = os.path.join('logs', 'gsutil_check_files')

def main(mode, ending, bucket):
    past_tense = f'{mode[:-1]}{ending}'
    with open(logfile, 'a+') as fh:
        print(datetime.datetime.now(), file=fh)

    if os.path.isfile('list_of_transfers'):
        with open('list_of_transfers', 'r') as fh:
            total = len(fh.read().splitlines())
    else:
        total = 0

    if os.path.isfile(f'{past_tense}_files'):
        with open(f'{past_tense}_files', 'r') as fh:
            previous = len(fh.read().splitlines())
    else:
        previous = 0

    if 'transfer' in mode:
        ut.shell_to_files(['gsutil', 'ls', f'gs://{bucket}/*.csv'], 'transferred_files', logfile)
        with open('transferred_files', 'r') as fh:
            current = len(fh.read().splitlines())
    else:
        current = len([fil for fil in os.listdir('downloads') if '.csv' in fil])

    with open(logfile, 'a+') as fh:
        print(f'Files on previous check = {str(previous)}', file=fh)
        print(f'Files on current check = {str(current)}', file=fh)
        print(f'Total transfers = {str(total)}', file=fh)
        print(f'Remaining transfers = {str(total - current)}', file=fh)

    if total == current:
        with open(f'{mode}_completed', 'w') as fch:
            print(f'{str(total)} files successfully {past_tense} from Earth Engine to bucket!', file=fch)
