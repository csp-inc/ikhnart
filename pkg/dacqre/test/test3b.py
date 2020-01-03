import os
import subprocess


backup_products = subprocess.run(['gsutil', 'ls', 'gs://dacqre-test3/csv_output/sample/backup/*.csv'], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')
products = subprocess.run(['gsutil', 'ls', 'gs://dacqre-test3/csv_output/sample/*.csv'], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')

check_backups_for = ['MET', 'DAYMET', 'LANDSAT_NDVI_EVI', 'LANDSAT_NBR']
check_main_for = ['MET', 'DAYMET', 'LANDSAT_NDVI_EVI', 'LANDSAT_NBR', 'MODIS']

def prod_exists(checked_prod, bucket_prods):
    for b_prod in bucket_prods:
        if checked_prod in b_prod:
            return True
    return False

def prods_exist(checked_prods, bucket_prods):
    files_exist = [prod_exists(c_prod, bucket_prods) for c_prod in checked_prods]
    if all(files_exist):
        return True
    else:
        return False
        
if prods_exist(check_main_for, products) and prods_exist(check_backups_for, backup_products):
    with open(os.path.join('test', 'results'), 'a+') as fh:
        print("Test 3b: PASSED", file=fh)
else:
    with open(os.path.join('test', 'results'), 'a+') as fh:
        print("Test 3b: FAILED", file=fh)

test_results = open('test/results', 'r')
print(test_results.read())
test_results.close()
