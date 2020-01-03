from . import tools
import yaml
import sys
import pkg_resources


if len(sys.argv) < 4:
    p_file = 'ee_yaml_src/{}_static_products.yaml'.format(sys.argv[2])
    l_file = 'ee_yaml_src/ll.yaml'
else:
    p_file = 'ee_yaml_src/{}'.format(sys.argv[3])
    l_file = 'ee_yaml_src/{}'.format(sys.argv[4])

with open(pkg_resources.resource_filename('ee_grab', p_file)) as products_y:
    static_raw = yaml.safe_load(products_y)
    static_base = {'products': static_raw}
with open(pkg_resources.resource_filename('ee_grab', l_file)) as ll_y:
    static_ll = yaml.safe_load(ll_y)
    
static_base.update(static_ll)
static_base['database'] = sys.argv[1]
static_base['service_json'] = '/root/service-ee.json'
static_out = tools.pull_static(**static_base)
