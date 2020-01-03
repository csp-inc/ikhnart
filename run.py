import os
import dacqre.main
import yaml
from bokeh.io import show

with open('run_parameters.yaml', 'r') as yfh:
    params = yaml.safe_load(yfh)
print(params)

def full_static():
    this_kw = dacqre.main.full_static_run(**params)
    return this_kw

def full():
    this_kw = dacqre.main.full_run(**params)
    return this_kw

def init_only():
    my_kw = dacqre.main.init(**params)
    if not my_kw:
        exit
    return my_kw

def submit_only():
    my_kw = dacqre.main.init(**params)
    if not my_kw:
        exit
    dacqre.main.make_yamls(**my_kw)
    dacqre.main.get_cloud_files(**my_kw)
    my_kw = dacqre.main.do_dates(**my_kw)
    dacqre.main.generate_tasks(in_diff_list=[], **my_kw)
    return my_kw

def continuation():
    my_kw = dacqre.main.init(**params)
    if not my_kw:
        exit
    dacqre.main.download_files(**my_kw)
    dacqre.main.make_yamls(**my_kw)
    dacqre.main.parse_files(in_diff_list=[], **my_kw)
    dacqre.main.move_downloads(**my_kw)
    dacqre.main.do_rsync_down(**my_kw)
    dacqre.main.do_aggregate(static='dynamic', **my_kw)
    dacqre.main.do_upload(**my_kw)
    dacqre.main.clean_up(**my_kw)
    show(dacqre.main.dataviz.generate_visualization(wd='output', collection=my_kw['collection']))
    return my_kw

if __name__ == '__main__':
    kw = locals()[params["run_mode"]]()

