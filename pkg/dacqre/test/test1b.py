import os
import subprocess


products = subprocess.run(['gsutil', 'ls', 'gs://dacqre-test1/csv_output/sample/LANDSAT_NBR*.csv'], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')[0]

if 'long' in products and 'sample' in products:
    with open(os.path.join('test', 'results'), 'a+') as fh:
        print("Test 1b: PASSED", file=fh)
else:
    with open(os.path.join('test', 'results'), 'a+') as fh:
        print("Test 1b: FAILED", file=fh)
