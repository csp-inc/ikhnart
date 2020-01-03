import os
import subprocess
import time


time.sleep(90)
products = subprocess.run(['gsutil', 'ls', 'gs://dacqre-test1/*.csv'], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')[0]

if 'LANDSAT_NBR' in products:
    with open(os.path.join('test', 'results'), 'a+') as fh:
        print("Test 1a: PASSED", file=fh)
else:
    with open(os.path.join('test', 'results'), 'a+') as fh:
        print("Test 1a: FAILED", file=fh)
