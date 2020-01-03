from . import tools
import os
import yaml
import sys
import pkg_resources

if len(sys.argv) < 4:
    p_file = 'ee_yaml_src/{}_dynamic_products.yaml'.format(sys.argv[2])
    l_file = 'ee_yaml_src/ll.yaml'
else:
    p_file = 'ee_yaml_src/{}'.format(sys.argv[3])
    l_file = 'ee_yaml_src/{}'.format(sys.argv[4])

with open(pkg_resources.resource_filename('ee_grab', p_file)) as products_y:
    ts_raw = yaml.safe_load(products_y)
    ts_base = {'products': ts_raw}
with open(pkg_resources.resource_filename('ee_grab', l_file)) as ll_y:
    ts_ll = yaml.safe_load(ll_y)
ts_base.update(ts_ll)
ts_base['database'] = sys.argv[1]
ts_base['service_json'] = '/root/service-ee.json'
ts_out = tools.pull_ts(**ts_base)
