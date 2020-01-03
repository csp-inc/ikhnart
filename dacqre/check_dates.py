import os
from . import utils as ut

class Product:
    def __init__(self, collection, **kw):
        self.name = collection
        self.cloud_date_file = 'cloud_files'

    def load_cloud_file(self):
        with open('cloud_files', 'r') as cloud_f:
            self.cloud_dates = cloud_f.read().splitlines()

    def load_cloud_dates(self):
        tmp_list = [os.path.basename(fil) for fil in self.cloud_dates]
        self.cloud_dict = {'_'.join(fil.split('_')[:-4]): fil.split('_')[-1].replace('.csv', '') for fil in tmp_list if 'long' in fil.split('_')[-2]}

    def gen_date_dict(self):
        self.load_cloud_file()
        self.load_cloud_dates()
        return self.cloud_dict

def main(**kw):
    my_product = Product(**kw)
    return my_product.gen_date_dict()
