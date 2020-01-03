import numpy as np
import yaml
import pandas as pd
import os
import sys
import shutil
from . import get_wrs


class Incoming:
    def __init__(self, collection: str, version: int, yaml_path: str, is_diff: bool, p_diff: bool=False, diff_file: str='', **kw):
        self.name = collection
        self.version = version
        self.yaml_path = yaml_path
        self.p_diff = p_diff
        if self.p_diff and is_diff:
            raw_df  = pd.read_csv(diff_file)
        elif is_diff:
            diff_df = pd.read_csv(diff_file)
            df_n    = pd.read_csv(os.path.join('collections', f'{self.name}_points_v{str(self.version)}.csv'))
            raw_df  = df_n[~df_n.PlotKey.isin(diff_df.PlotKey.values)]
        else:
            raw_df  = pd.read_csv(os.path.join('collections', f'{self.name}_points_v{str(self.version)}.csv'))
        new_df = raw_df[['PlotKey', 'Latitude', 'Longitude']]
        self.df = new_df.drop_duplicates('PlotKey')
        self.df.reset_index(drop=True, inplace=True)
        self.latlons = [(lat, lon) for lat, lon in zip(self.df['Latitude'], self.df['Longitude'])]
        self.prdf = None


    def make_pathrows(self):
        conv = get_wrs.ConvertToWRS()
        pathrows = [conv.get_wrs(*latlon) for latlon in self.latlons]
        self.df['pathrows'] = pathrows
        allpathrows = set([it for sublist in pathrows for it in sublist])
        all_prs = list(allpathrows)
        all_prs.sort()
        self.prdf = pd.DataFrame(all_prs)
        self.prdf.rename(columns={0: "pr"}, inplace=True)
        pr_matches = []
        for pr in self.prdf['pr']:
            pr_matches.append([idx for (idx, lpr) in zip(self.df.PlotKey, self.df['pathrows']) if pr in lpr])
        self.prdf['matches'] = pr_matches

    def make_yaml(self):
        if self.prdf is not None:
            ll_dict = {'pathrows': {row.pr: [x for x in row.matches] for row in self.prdf.itertuples(index=False)}}
        else:
            ll_dict = {}
        paths = [int(x.split('_')[1]) for x in ll_dict['pathrows'].keys()]
        rows = [int(x.split('_')[-1]) for x in ll_dict['pathrows'].keys()]
        self.ll_map = pd.DataFrame([x for x in range(len(paths))], columns=['PR_Key'])
        self.ll_map['Path'] = paths
        self.ll_map['Row'] = rows
        self.ll_map.to_csv(os.path.join(self.yaml_path, f'pr_keys_{self.name}_v{self.version}.csv'), index=False)
        ll_dict['points'] = {row.PlotKey: [row.Latitude, row.Longitude] for row in self.df.itertuples(index=False)}
        ll_dict['name'] = self.name
        self.yaml_dict = {'latlons': ll_dict}
        if self.p_diff:
            with open(os.path.join(self.yaml_path, 'll_diff.yaml'), 'w') as out_f:
                yaml.dump(self.yaml_dict, out_f, default_flow_style=False)
        else:
            with open(os.path.join(self.yaml_path, 'll.yaml'), 'w') as out_f:
                yaml.dump(self.yaml_dict, out_f, default_flow_style=False)
            shutil.copy(os.path.join(self.yaml_path, 'll.yaml'), os.path.join(self.yaml_path, f'll_{self.name}_v{str(self.version)}.yaml'))

def main(**kw):
    if kw["is_diff"]:
        my_d_incoming = Incoming(p_diff=True, **kw)
        my_d_incoming.make_pathrows()
        my_d_incoming.make_yaml()
        my_incoming = Incoming(p_diff=False, **kw)
        my_incoming.make_pathrows()
        my_incoming.make_yaml()
    else:
        my_incoming = Incoming(**kw)
        my_incoming.make_pathrows()
        my_incoming.make_yaml()
