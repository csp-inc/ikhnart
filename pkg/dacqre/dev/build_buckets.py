import os
from glob import glob
import subprocess

collections = glob('collections/*.csv')
bucket_names = [(os.path.basename(f).split('_')[0]) for f in collections]
print(bucket_names)
for bucket_name in bucket_names:
    cmd = ['gsutil', 'mb', '-p', 'greenwave-257417', '-l', 'us-west2', 'gs://%s'%bucket_name]
    out = subprocess.Popen(cmd, stdout=subprocess.PIPE) 

