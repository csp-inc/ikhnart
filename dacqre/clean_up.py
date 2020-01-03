import os
import shutil
from . import utils as ut

def remove_files(byebye: list):
    for fil in byebye:
        ut.remove(fil)

def main(in_collection):
    files_to_remove = ['list_of_transfers', 'cloud_files', 'terradat_latest_version']
    copy_directories = {os.path.join('uploads', in_collection): os.path.join('output', in_collection)}

    remove_files(files_to_remove)

#    for src, dst in copy_directories.items():
    ut.shell_exec(['rsync', '-d', f'{os.path.join("uploads", in_collection)}/', os.path.join('output', in_collection)])
    ut.shell_exec(['rsync', '-d', f'{os.path.join("uploads", in_collection, "backup")}/', os.path.join('output', in_collection, 'backup')])
#        for src_file_base in os.listdir(src):
#            src_file = os.path.join(src, src_file_base)
#            dst_file = os.path.join(dst, src_file_base)
#            if os.path.isfile(dst_file):
#                if os.stat(src_file).st_mtime - os.stat(dst_file).st_mtime > 1:
#                    shutil.copy2(src_file, dst_file)
#
