import os
import subprocess
import datetime
from . import utils as ut


logfile = os.path.join('logs', 'gsutil_dates_log')

def main(gsutil_command, files_to_check, command_out_file):
    with open(logfile, 'a+') as fh:
        print(datetime.datetime.now(), file=fh)

    with open(logfile, 'r') as fh:
        num_lines = fh.read().splitlines()

    ut.shell_to_files(['gsutil', gsutil_command, files_to_check], command_out_file, logfile)

    with open(logfile, 'r') as fh:
        num_new_lines = fh.read().splitlines()

    with open(logfile, 'a+') as fh:
        if num_new_lines == num_lines:
            print('Successful file listing!', file=fh)
            return True
        else:
            print('No files found.', file=fh)
            return False
