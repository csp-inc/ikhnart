import os


with open(os.path.join('logs', 'images_not_available'), 'r') as fh:
    products = fh.read().split('\n')

if 'MODIS' in products:
    with open(os.path.join('test', 'results'), 'a+') as fh:
        print("Test 0: PASSED", file=fh)
else:
    with open(os.path.join('test', 'results'), 'a+') as fh:
        print("Test 0: FAILED", file=fh)
