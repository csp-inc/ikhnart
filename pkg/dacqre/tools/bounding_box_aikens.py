import numpy as np
import yaml


def draw_n_samples(in_min, in_max, n=25):
    return (in_max - in_min) * np.random.random_sample(n) + in_min

x = [-111, -110.75]
y = [41.19, 42.81]

lons = draw_n_samples(*x)
lats = draw_n_samples(*y)

latlons = [(lat, lon) for lat, lon in zip(lats, lons)]
yaml_dict = {'landsat_latlons': {f'southern_random_{str(pt).zfill(2)}': [float(x) for x in list(latlon)] for pt, latlon in enumerate(latlons)}}
with open('my_yaml.yml', 'w') as out_f:
    yaml.dump(yaml_dict, out_f, default_flow_style=False)
