import os
import dacqre.clean_up as d_clean
import yaml
import glob
import shutil


### WARNING: This will clear all local files for a given collection. Be sure you want to do this! ###

with open('run_parameters.yaml', 'r') as yfh:
    params = yaml.safe_load(yfh)
print(params)

def init(collection, bucket, **kw):
    directories = {'whole': [os.path.join(x, collection) for x in ['output', 'uploads']],
            'partial': [os.path.join('backup_downloads', bucket), 'config', 'collections']}
    return directories

def clear_whole(in_dirs):
    for wdir in in_dirs['whole']:
        print(wdir)
        shutil.rmtree(wdir)

def clear_partial(in_dirs):
    for fdir in in_dirs['partial']:
        print(fdir)
        byefiles = glob.glob(os.path.join(fdir, f'*{params["collection"]}*'))
        print(byefiles)
        d_clean.remove_files(byefiles)

def clear_all(in_dirs):
    clear_whole(in_dirs)
    clear_partial(in_dirs)

if __name__ == '__main__':
    my_dirs = init(**params)
    clear_all(my_dirs)
