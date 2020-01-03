import os
import subprocess
from glob import glob
import yaml

def create_yaml(collection_name, run_mode='full'):
    if run_mode=='full':
        my_vars = ['LANDSAT_NDVI_EVI', 'MODIS', 'TERRACLIMATE', 'MCD12Q1', 'MCD12Q2']
    elif run_mode=='full_static':
        my_vars = ['GLOBAL_ELEVATION']
    run_yaml = {'collection': collection_name,\
            'bucket':collection_name,\
            'run_mode':run_mode,\
            'my_vars':my_vars,\
            'end_date':'2020-01-01',\
            'default_wide':False}
    with open(out_yaml, 'w') as stream:
        yaml.dump(run_yaml, stream)
    return()

def check_bucket(collection_name, project='greenwave-257417'):
    #checks if bucket exists, if not, create it
    print(f'Making {collection_name} bucket')
    gsutil_cmd = ['gsutil', 'mb', '-p', 'greenwave-257417', '-l', 'us-west2', \
	f'gs://{collection_name.lower()}']
    subprocess.Popen(gsutil_cmd).wait()
    return()

def run_dacqre_collection(collection_name):
    #make bucket if it doesn't exist
    check_bucket(collection_name)
    #step two look up the collections folder
    create_yaml(collection_name, run_mode='full_static')
    #step three run.py
    subprocess.Popen(run_cmd).wait()
    #step three create_another yaml that has run mode 
    create_yaml(collection_name)
    subprocess.Popen(run_cmd).wait()
    return(print(f'Finished for {collection_name}!'))

if __name__ == "__main__":
    out_yaml = 'run_parameters.yaml'
    run_cmd = ['python3', 'run.py']
    collections = [os.path.basename(f).split('_')[0] for f in sorted(glob('collections/*.csv'))]

    for collection_name in collections:
        run_dacqre_collection(collection_name)

