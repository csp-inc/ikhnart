import os
import yaml
from dacqre import datavisualize as dataviz
from bokeh.io import show

with open('run_parameters.yaml', 'r') as yfh:
    params = yaml.safe_load(yfh)

if __name__ == '__main__':
    wd = 'output'
    collection = params['collection']
    tabs = dataviz.generate_visualization(wd=wd, collection=collection)
    show(tabs)
