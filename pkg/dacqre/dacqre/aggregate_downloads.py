import glob, os
import sys
import pandas as pd
import json
import numpy as np
from . import utils as ut
import yaml
import shutil


class Staticvar:
    def __init__(self, my_dataset, myvar, myversion):
        self.dataset = my_dataset
        self.name = myvar
        self.version = myversion
        self.diff = False
        if os.path.isfile(f'{self.dataset}_diff.csv'):
            self.diff = True
        self.csv_files = [fil for fil in glob.glob(os.path.join('output', self.dataset, f'{self.name}_{self.dataset}*.csv'))]
        self.delete_files = [fil for fil in self.csv_files if 'diff' in fil]
        self.old_backups = [fil for fil in glob.glob(os.path.join('uploads', self.dataset, 'backup', f'{self.name}_{self.dataset}*.csv'))]
        self.all_versions = list(set([int(fil.split('_')[-1].replace('.csv', '').replace('v', '')) for fil in self.csv_files]))
        self.all_versions.sort()
        self.to_backup_files = []
        if len(self.all_versions) > 1:
            self.to_backup_files = [fil for fil in self.csv_files if str(self.all_versions[0]) in fil]


    def make_long_csv(self):
        self.long_csv = pd.concat(map(pd.read_csv, self.csv_files))
        self.long_csv.sort_values(['location'], inplace=True)
        self.long_csv.drop_duplicates(inplace=True)
        self.varlist = self.long_csv.drop(['location'], axis=1).columns

    def write_var_csvs(self):
        self.long_csv.to_csv(os.path.join('uploads', self.dataset, f'{self.name}_{self.dataset}_v{self.version}.csv'), index=False)

    def big_process(self):
        print(self.name)
        if len(self.csv_files) == 1:
            print('Just copy')
            sys.stdout.write(f'No new files to aggregate.\n')
            shutil.copy(self.csv_files[0], self.csv_files[0].replace('output', 'uploads'))
        elif len(self.csv_files) == 0:
            print('Do Nothing')
            sys.stdout.write(f'No files exist for this variable.\n')
        else:
            print('Standard Procedure')
            sys.stdout.write(f'Making long csv.\n')
            self.make_long_csv()
            sys.stdout.write(f'Writing csvs to disk.\n')
            self.write_var_csvs()
            if self.to_backup_files:
                sys.stdout.write(f'Backing up old static csvs.\n')
                for fil in self.to_backup_files:
                    os.rename(fil, fil.replace('output', 'uploads').replace(self.name, os.path.join('backup', self.name)))
                sys.stdout.write(f'Removing old static backups.\n')
                for fil in self.old_long_backups:
                    ut.remove(fil)

class Variable:
    def __init__(self, my_dataset, myvar, myversion, myll, mydefaultwide):
        self.dataset = my_dataset
        self.name = myvar
        self.plot_ll = myll
        self.wide_bool = mydefaultwide
        if 'MET' in self.name:
            self.wide_bool = False
        self.version = myversion
        self.diff = False
        if os.path.isfile(f'{self.dataset}_diff.csv'):
            self.diff = True
        self.csv_files = [fil for fil in glob.glob(os.path.join('output', self.dataset, f'{self.name}_{self.dataset}*.csv')) if 'long' in fil]
        self.dates = list(set([fil.split('_')[-1].replace('.csv', '') for fil in self.csv_files]))
        self.dates.sort()
        self.delete_files = [fil for fil in self.csv_files if 'diff' in fil]
        self.old_long_backups = [fil for fil in glob.glob(os.path.join('uploads', self.dataset, 'backup', f'{self.name}_{self.dataset}*.csv')) if 'long' in fil]
        self.old_wide_backups = [fil for fil in glob.glob(os.path.join('uploads', self.dataset, 'backup', f'{self.name}_{self.dataset}*.csv')) if 'wide' in fil]
        self.to_backup_files = []
        if len(self.dates) > 1:
            self.to_backup_files = [fil for fil in self.csv_files if self.dates[0] in fil]

    def make_long_csv(self):
        self.long_csv = pd.concat(map(pd.read_csv, self.csv_files))
        self.long_csv.sort_values(['img_date', 'location'], inplace=True)
        self.long_csv.drop_duplicates(inplace=True)
        self.varlist = self.long_csv.drop(['img_date', 'location'], axis=1).columns

    def make_wide_csv(self):
        self.wide = self.long_csv.pivot_table(index=['location'], columns='img_date', values=self.varlist)
        self.wide_csv = self.plot_ll.merge(self.wide, left_on='PlotKey', right_index=True)
        self.wide_csv.sort_index(inplace=True)
        self.old_wides = [fil for fil in glob.glob(os.path.join('output', self.dataset, f'{self.name}_{self.dataset}*.csv')) if 'wide' in fil]
        sys.stdout.write(f'Backing up old wide csvs.\n')
        for fil in self.old_wides:
            os.rename(fil, fil.replace('output', 'uploads').replace(self.name, os.path.join('backup', self.name)))
        sys.stdout.write(f'Removing old wide backups.\n')
        for fil in self.old_wide_backups:
            ut.remove(fil)

    def get_last_date(self):
        self.dates = self.long_csv.img_date.copy()
        self.dates.sort_values(inplace=True)
        self.last_date = self.dates.iloc[-1]

    def write_var_csvs(self):
        written_types = ['long']
        if self.wide_bool:
            written_types.append('wide')
        for my_f in written_types:
            getattr(self, f'{my_f}_csv').to_csv(os.path.join('uploads', self.dataset, f'{self.name}_{self.dataset}_v{self.version}_{my_f}_{self.last_date}.csv'), index=False)

    def big_process(self):
        print(self.name)
        print('Will we be making a wide format version?:', self.wide_bool)
        if len(self.csv_files) == 1 and not self.wide_bool:
            print('Just copy')
            sys.stdout.write(f'No new files to aggregate.\n')
            shutil.copy(self.csv_files[0], self.csv_files[0].replace('output', 'uploads'))
        elif len(self.csv_files) == 0:
            print('Do Nothing')
            sys.stdout.write(f'No files exist for this variable.\n')
        else:
            print('Standard Procedure')
            sys.stdout.write(f'Making long csv.\n')
            self.make_long_csv()
            sys.stdout.write('Getting last date.\n')
            self.get_last_date()
            if self.wide_bool:
                sys.stdout.write(f'Making wide csv.\n')
                self.make_wide_csv()
            sys.stdout.write(f'Writing csvs to disk.\n')
            self.write_var_csvs()
            if self.to_backup_files:
                sys.stdout.write(f'Backing up old long csvs.\n')
                for fil in self.to_backup_files:
                    os.rename(fil, fil.replace('output', 'uploads').replace(self.name, os.path.join('backup', self.name)))
                sys.stdout.write(f'Removing old long backups.\n')
                for fil in self.old_long_backups:
                    ut.remove(fil)

def main(in_mode, in_dataset, in_var, in_version, in_ll, in_default_wide):
    if 'dynamic' in in_mode:
        my_variable = Variable(in_dataset, in_var, in_version, in_ll, in_default_wide)
    else:
        my_variable = Staticvar(in_dataset, in_var, in_version)
    my_variable.big_process()
    return my_variable

def full_aggregate(static='dynamic', **kw):
    plot_csv = pd.read_csv(os.path.join('collections', f'{kw["collection"]}_points_v{kw["version"]}.csv'))
    plot_ll = plot_csv[['PlotKey', 'Latitude', 'Longitude']].copy()
    if os.path.exists(os.path.join(kw["yaml_path"], f'{kw["collection"]}_{static}_products.yaml')):
        with open(os.path.join(kw["yaml_path"], f'{kw["collection"]}_{static}_products.yaml'), 'r') as in_f:
            dyn_vars = yaml.safe_load(in_f)
    else:
        dyn_vars = {}
    if dyn_vars:
        for varname, v in dyn_vars.items():
            if varname in kw["my_vars"] or 'all' in kw["my_vars"]:
                main(static, kw["collection"], varname, kw["version"], plot_ll, kw["default_wide"])
