import glob, os
import sys
import pandas as pd
import json
import numpy as np
from . import utils as ut
import yaml


class Variable:
    def __init__(self, my_dir, my_dataset, myvar, myvarlist, myversion, static, diff, **kw):
        self.fullpath = my_dir
        self.dataset = my_dataset
        self.yaml_path = kw["yaml_path"]
        self.name = myvar
        self.varlist = myvarlist
        self.version = myversion
        if 'LANDSAT_NDVI_EVI' in self.name:
            self.pr_keys_df = pd.read_csv(os.path.join(self.yaml_path, f'pr_keys_{self.dataset}_v{self.version}.csv'))
            self.varlist = ['NDVI', 'EVI', 'sensor', 'pathrow']
            self.mask_dict = {
                'clear':
                    [
                        '0'    # not clear
                    ],
                'rad_fill':
                    [
                        '1'    # invalid
                    ],
                'rad_B1':
                    [
                        '1'    # saturated
                    ],
                'rad_B2':
                    [
                        '1'    # saturated
                    ],
                'rad_B3':
                    [
                        '1'    # saturated
                    ],
                'rad_B4':
                    [
                        '1'    # saturated
                    ],
                'rad_B5':
                    [
                        '1'    # saturated
                    ]
                }
        elif 'MODIS' in self.name:
            self.varlist = ['NDVI', 'EVI', 'DayOfYear']
            self.mask_dict = {
                'bin_code':
                    [
                        '01',
                        '10',
                        '11'
                    ]
                }
        self.static = False
        if 'static' in static:
            self.static = True
        self.diff = diff
        self.files_exist = False

    def aux_files_exist_check(self):
        if os.path.isdir(self.fullpath):
            self.csv_src_files_maybe_valid = glob.glob(os.path.join(self.fullpath, f'{self.name}_{self.dataset}*.csv'))
            self.csv_src_files = [fil for fil in self.csv_src_files_maybe_valid if os.path.getsize(fil) > 5]
            if len(self.csv_src_files) > 0:
                self.files_exist = True

    def qa_mask_csv(self):
        for col, val_list in self.mask_dict.items():
            for val in val_list:
                self.csv.loc[self.csv[col] == val, 'NDVI'] = np.nan
                self.csv.loc[self.csv[col] == val, 'EVI'] = np.nan

    def concat_csv(self):
        self.csv = pd.concat(map(pd.read_csv, self.csv_src_files))
        print('done concatenating')
        if 'LANDSAT_NDVI_EVI' in self.name:
            self.csv['bin_code'] = self.bin_codes()
            self.csv['clear'] = [bin_string[-2] for bin_string in self.csv['bin_code']]

            self.csv['radsat_bin_code'] = self.bin_codes(in_col='radsat_qa', length=12, default=1)
            self.csv['rad_fill'] = [bin_string[-1] for bin_string in self.csv['radsat_bin_code']]
            self.csv['rad_B1'] = [bin_string[-2] for bin_string in self.csv['radsat_bin_code']]
            self.csv['rad_B2'] = [bin_string[-3] for bin_string in self.csv['radsat_bin_code']]
            self.csv['rad_B3'] = [bin_string[-4] for bin_string in self.csv['radsat_bin_code']]
            self.csv['rad_B4'] = [bin_string[-5] for bin_string in self.csv['radsat_bin_code']]
            self.csv['rad_B5'] = [bin_string[-6] for bin_string in self.csv['radsat_bin_code']]
            self.csv['sensor'] = [int(x) for x in self.csv['sensor']]
            self.csv['pathrow'] = [int(self.pr_keys_df.loc[self.pr_keys_df['Path'] == p].loc[self.pr_keys_df['Row'] == r]['PR_Key']) for p,r in zip(self.csv['path'], self.csv['row'])]
            print(self.csv['pathrow'])
            print('done making pathrows')

            self.csv.drop_duplicates(subset=['location', 'img_date', 'sensor', 'pathrow'], inplace=True)
        elif 'MODIS' in self.name:
            self.csv['bin_code'] = self.bin_codes(in_col='SummaryQA', length=2, default=3)
            self.csv.drop_duplicates(subset=['location', 'img_date'], inplace=True)
        elif self.static:
            self.csv.drop_duplicates(subset=['location'], inplace=True)
        else:
            self.csv.drop_duplicates(subset=['location', 'img_date'], inplace=True)
        print('done dropping duplicates')


    def bin_codes(self, in_col='pixel_qa', length=11, default=61):
        no_nans_in_bin_code = [int(val) if not np.isnan(val) else default for val in self.csv[in_col]]
        return [np.binary_repr(val).zfill(length) for val in no_nans_in_bin_code]

    def make_plot_csv(self):
        if self.diff:
            self.plot_csv = pd.read_csv(os.path.join('collections', f'{self.dataset}_diff.csv'))
        else:
            self.plot_csv = pd.read_csv(os.path.join('collections', f'{self.dataset}_points_v{self.version}.csv'))
        self.plot_ll = self.plot_csv[['PlotKey', 'Latitude', 'Longitude']].copy()

    def make_long_csv(self):
        if self.static:
            self.long = self.csv.copy()
            self.long.dropna(how='any', inplace=True)
            self.long.drop_duplicates()
            self.long.sort_values(['location'], inplace=True)
        else:
            self.long = self.csv[['location', 'img_date', *self.varlist]].copy()
            self.long.dropna(subset=self.varlist, how='any', inplace=True)
            self.long.drop_duplicates()
            self.long.sort_values(['img_date', 'location'], inplace=True)

    def get_last_date(self):
#        self.dates = self.long.img_date.copy()
#        self.dates.sort_values(inplace=True)
        if not hasattr(self.long, 'img_date'):
            return False
        elif not self.long.img_date.empty:
            return self.long.img_date.iloc[-1]
        else:
            return False


    def write_var_csvs(self):
        if self.diff:
            self.long.to_csv(os.path.join('output', self.dataset, f'{self.name}_{self.dataset}_v{self.version}_diff_long_{self.last_date}.csv'), index=False)
        else:
            if self.last_date:
                self.long.to_csv(os.path.join('output', self.dataset, f'{self.name}_{self.dataset}_v{self.version}_long_{self.last_date}.csv'), index=False)
            elif self.static:
                self.long.to_csv(os.path.join('output', self.dataset, f'{self.name}_{self.dataset}_v{self.version}.csv'), index=False)
            else:
                sys.stdout.write(f'{self.name} has no valid data points, skipping write.\n')


    def big_process(self):
        sys.stdout.write(f'Parsing {self.name} data for {self.dataset}.\n')
        self.aux_files_exist_check()
        if not self.files_exist:
            sys.stdout.write(f'There are no files for {self.name} for {self.dataset} points, therefore no parsing will be done.\n')
            return
        sys.stdout.write(f'Concatenating {self.name} files for {self.dataset}.\n')
        self.concat_csv()
        self.make_plot_csv()
        if 'LANDSAT_NDVI_EVI' in self.name or 'MODIS' in self.name:
            sys.stdout.write(f'Creating mask.\n')
            self.qa_mask_csv()
        sys.stdout.write(f'Making long csv.\n')
        self.make_long_csv()
        sys.stdout.write('Getting last date.\n')
        self.last_date = self.get_last_date()
        sys.stdout.write(f'Writing long csvs to disk.\n')
        self.write_var_csvs()
        return True

def main(in_dataset, in_var, var_list, in_version, static, diff=False, **kw):
    my_variable = Variable('downloads', in_dataset, in_var, var_list, in_version, static, diff, **kw)
    _ = my_variable.big_process()
    print(f'done with {in_var}')

def full_parse(collection, version, alt_yaml=False, static='dynamic', **kw):
    if alt_yaml:
        with open(alt_yaml, 'r') as in_f:
            dyn_vars = yaml.safe_load(in_f)
        if 'diff' in alt_yaml:
            for k, v in dyn_vars.items():
                if k in kw["my_vars"] or 'all' in kw["my_vars"]:
                    main(collection, k, v['selector_list'], version, static, diff = True, **kw)
        else:
            for k, v in dyn_vars.items():
                if k in kw["my_vars"] or 'all' in kw["my_vars"]:
                    main(collection, k, v['selector_list'], version, static, **kw)
    else:
        with open(os.path.join(kw["yaml_path"], f'{collection}_{static}_products.yaml'), 'r') as in_f:
            dyn_vars = yaml.safe_load(in_f)
        for k, v in dyn_vars.items():
            if k in kw["my_vars"] or 'all' in kw["my_vars"]:
                if 'static' in static:
                    main(collection, k, [], version, static, **kw)
                else:
                    main(collection, k, v['selector_list'], version, static, **kw)
