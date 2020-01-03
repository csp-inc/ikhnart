from time import sleep
from bokeh.io import show
from . import utils as ut
from . import make_yaml as myaml
from . import gsutil_get_dates as gs_g_date
from . import check_dates as c_date
from . import gsutil_check_ee as gs_c_ee
from . import parse_downloads as parse_dl
from . import aggregate_downloads as agg_dl
from . import clean_up as clean
from . import datavisualize as dataviz
from .dynamic import tools as ts
from .static import tools as get_static
import os
import yaml
import shutil
import glob


def check_completed(mode='transfers', ending='red', interval=60, bucket='blm-aim'):
    past_tense = f'{mode[:-1]}{ending}'
    process_complete = False
    while not process_complete:
        gs_c_ee.main(mode, ending, bucket)
        if os.path.isfile(f'{mode}_completed'):
            with open(f'{mode}_completed', 'r') as fh:
                f_contents = fh.read()
                if f'files successfully {past_tense}' in f_contents:
                    process_complete = True
                    ut.remove(f'{mode}_completed')
                    if 'transfers' in mode:
                        ut.remove(f'{past_tense}_files')
                    return int(f_contents.split()[0])
        else:
            sleep(interval)

def get_yaml_keys(**kw):
    with open(os.path.join(kw["yaml_path"], f'{kw["collection"]}_dynamic_products.yaml')) as d_products:
        dynamic_keys = yaml.safe_load(d_products).keys()
    with open(os.path.join(kw["yaml_path"], f'{kw["collection"]}_static_products.yaml')) as s_products:
        static_keys = yaml.safe_load(s_products).keys()
    all_keys = [k for k in dynamic_keys] + [k for k in static_keys]
    if kw["is_diff"]:
        if os.path.isfile(os.path.join(kw["yaml_path"], f'{kw["collection"]}_diff_products.yaml')):
            with open(os.path.join(kw["yaml_path"], f'{kw["collection"]}_diff_products.yaml')) as df_products:
                diff_keys = yaml.safe_load(df_products).keys()
            all_keys += [k for k in diff_keys]
    return list(set(all_keys))

def warn_provided_vars(**kw):
    if 'all' in kw["my_vars"]:
        return False
    else:
        config_keys = get_yaml_keys(**kw)
        bad_vars = []
        for var in kw["my_vars"]:
            if var not in config_keys:
                bad_vars.append(var)
        return ', '.join(bad_vars)

def generate_tasks(in_diff_list, **kw):
    in_kw = {'p_file': os.path.join(kw["yaml_path"], f'{kw["collection"]}_dynamic_products.yaml')}
    in_kw['l_file'] = kw["operational_ll_file"]
    in_kw['diff_run'] = False
    if in_diff_list:
        in_kw['p_file'] = in_diff_list[0]
        in_kw['l_file'] = in_diff_list[1]
        in_kw['diff_run'] = True
    in_kw.update(kw)
    with open(in_kw["p_file"]) as products_y:
        ts_raw = yaml.safe_load(products_y)
    ts.main(**in_kw)

def generate_static_tasks(in_diff_list, **kw):
    in_kw = {'p_file': os.path.join(kw["yaml_path"], f'{kw["collection"]}_static_products.yaml')}
    in_kw['l_file'] = kw["operational_ll_file"]
    if in_diff_list:
        in_kw['p_file'] = in_diff_list[0]
        in_kw['l_file'] = in_diff_list[1]
    in_kw.update(kw)
    get_static.main(**in_kw)

def check_transfers(**kw):
    num_transfers = check_completed(bucket=kw["bucket"])
    if num_transfers > 0:
        return True
    else:
        return False

def download_files(**kw):
    if not os.path.isdir('downloads'):
        os.makedirs('downloads')
    ut.shell_exec(['gsutil', '-m', 'cp', f'gs://{kw["bucket"]}/*.csv', 'downloads/'])

def check_downloads(**kw):
    num_downloads = check_completed(mode='downloads', ending='ed', interval=5, bucket=kw["bucket"])
    if num_downloads > 0:
        return True
    else:
        return False

def parse_files(in_diff_list, static='dynamic', **kw):
    if in_diff_list:
        parse_dl.full_parse(alt_yaml=in_diff_list[0], static=static, **kw)
    else:
        parse_dl.full_parse(alt_yaml=False, static=static, **kw)

def move_downloads(**kw):
    for fil in os.listdir('downloads'):
        if '.csv' in fil:
            os.rename(os.path.join('downloads', fil), os.path.join('backup_downloads', kw["bucket"], fil))

def ee_submit_download_remove_static(diff_list = [], **kw):
    generate_static_tasks(diff_list, **kw)
    transfer_success = check_transfers(**kw)
    if not transfer_success:
        return False
    download_files(**kw)
    download_success = check_downloads(**kw)
    if not download_success:
        return False
    parse_files(diff_list, static='static', **kw)
    move_downloads(**kw)
    return True

def ee_submit_download_remove(diff_list = [], **kw):
    generate_tasks(diff_list, **kw)
    transfer_success = check_transfers(**kw)
    if not transfer_success:
        return False
    download_files(**kw)
    download_success = check_downloads(**kw)
    if not download_success:
        return False
    parse_files(diff_list, **kw)
    move_downloads(**kw)
    return True

def init(**kw):
    print('init')
    ut.remove('list_of_transfers')
    ut.remove(os.path.join('logs', 'images_not_available'))
    ut.remove(os.path.join('logs', 'gsutil_dates_log'))
    if os.path.isdir(os.path.join('authentication', '.boto')):
        shutil.rmtree(os.path.join('authentication', 'credentials'))
        shutil.rmtree(os.path.join('authentication', '.boto'))
        print('Authentication failure... perhaps you have not run "init_authenticate.sh"?')
        return {}
    if os.path.isdir(os.path.join('authentication', 'credentials')):
        shutil.rmtree(os.path.join('authentication', 'credentials'))
        shutil.rmtree(os.path.join('authentication', '.boto'))
        print('Authentication failure... perhaps you have not run "init_authenticate.sh"?')
        return {}
    if not os.path.isdir(os.path.join('backup_downloads', kw["bucket"])):
        os.makedirs(os.path.join('backup_downloads', kw["bucket"]))
    if not os.path.isdir(os.path.join('output', kw["collection"], 'backup')):
        os.makedirs(os.path.join('output', kw["collection"], 'backup'))
    if not os.path.isdir(os.path.join('uploads', kw["collection"], 'backup')):
        os.makedirs(os.path.join('uploads', kw["collection"], 'backup'))

    collection_files = [fil for fil in glob.glob(os.path.join('collections', f'{kw["collection"]}_points_*.csv'))]
    collection_file_versions_raw = [fil.split('_')[-1].replace('.csv', '').replace('v', '') for fil in collection_files]
    try:
        collection_file_versions = list(set([int(x) for x in collection_file_versions_raw]))
    except ValueError:
        print('You need to specify a version number for your collection, which can take the format:')
        print('<collection_name>_points_v<version>.csv, where <version> is an integer')
        return {}
    else:
        print(all([isinstance(x, int) for x in collection_file_versions]))
        if len(collection_file_versions) < 1:
            print('You need to specify a version number for your collection, which can take the format:')
            print('<collection_name>_points_v<version>.csv, where <version> is an integer')
            return {}

    collection_file_versions.sort()
    kw["version"] = str(collection_file_versions[-1])
    kw["yaml_path"] = os.path.join('config')
    kw["ll_file"] = os.path.join(kw["yaml_path"], f'll_{kw["collection"]}_v{kw["version"]}.yaml')
    kw["operational_ll_file"] = os.path.join(kw["yaml_path"], 'll.yaml')
    kw["diff_file"] = os.path.join('collections', f'{kw["collection"]}_diff.csv')
    kw["collection_file"] = os.path.join('collections', f'{kw["collection"]}_points_v{kw["version"]}.csv')
    if not os.path.isfile(kw["collection_file"]):
        print('You have not provided a collection file that matches the name of the collection specified in "run_parameters.yaml". Please provide the appropriate csv!\nNow Exiting...')
        return {}
    bucket_files = ut.shell_exec(['gsutil', 'ls', f'gs://{kw["bucket"]}'], my_out=True)[-1].decode('utf-8').split('\n')[:-1]
    for fil in bucket_files:
        if '404' in fil and 'BucketNotFound' in fil:
            print('The bucket you have specified in run_parameters is not accessible or does not exist.')
            return {}
        if '403' in fil:
            print('The bucket you have specified in run_parameters is not accessible or does not exist.')
            return {}
    kw["is_diff"] = False
    if os.path.isfile(kw["diff_file"]):
        kw["is_diff"] = True
    return kw

def yaml_diff_copy(yaml_type, **kw):
    if not os.path.isfile(os.path.join(kw["yaml_path"], f'{kw["collection"]}_{yaml_type}_products.yaml')):
        shutil.copy(os.path.join(kw["yaml_path"], f'initial_dynamic_products.yaml'), os.path.join(kw["yaml_path"], f'{kw["collection"]}_{yaml_type}_products.yaml'))

def yaml_copy(yaml_type, **kw):
    if not os.path.isfile(os.path.join(kw["yaml_path"], f'{kw["collection"]}_{yaml_type}_products.yaml')):
        shutil.copy(os.path.join(kw["yaml_path"], f'initial_{yaml_type}_products.yaml'), os.path.join(kw["yaml_path"], f'{kw["collection"]}_{yaml_type}_products.yaml'))

def make_yamls(**kw):
    print('make_yamls')
    if os.path.isfile(kw["ll_file"]):
        shutil.copy(kw["ll_file"], os.path.join(kw["yaml_path"], 'll.yaml'))
    else:
        myaml.main(**kw)
    yaml_copy('dynamic', **kw)
    yaml_copy('static', **kw)
    yaml_diff_copy('diff', **kw)

def get_cloud_files(**kw):
    print('get_cloud_files')
    dates_exist = gs_g_date.main('ls', f'gs://{kw["bucket"]}/csv_output/{kw["collection"]}/*.csv', 'cloud_files')

def do_dates(**kw):
    print('update_date_params')
    kw['dates_dict'] = c_date.main(**kw)
    return kw

def submit_jobs(**kw):
    print('submitting_dynamic_jobs')
    if os.path.isfile(kw["diff_file"]):
        diff_process = ee_submit_download_remove(diff_list = [os.path.join(kw["yaml_path"], f'{kw["collection"]}_diff_products.yaml'), 'll_diff.yaml'], **kw)
    else:
        diff_process = False
    if os.path.isfile(os.path.join(kw["yaml_path"], f'{kw["collection"]}_dynamic_products.yaml')):
        update_process = ee_submit_download_remove(**kw)
    else:
        update_process = False
    if diff_process or update_process:
        return True
    else:
        return False

def submit_jobs_static(**kw):
    print('submitting_static_jobs')
    if os.path.isfile(kw["diff_file"]):
        diff_process = ee_submit_download_remove_static(diff_list = [os.path.join(kw["yaml_path"], f'{kw["collection"]}_diff_products.yaml'), 'll_diff.yaml'], **kw)
    else:
        diff_process = False
    if os.path.isfile(os.path.join(kw["yaml_path"], f'{kw["collection"]}_static_products.yaml')):
        static_process = ee_submit_download_remove_static(**kw)
    else:
        static_process = False
    if diff_process or static_process:
        return True
    else:
        return False

def do_rsync_down(**kw):
    print('rsync')
    ut.shell_exec(['gsutil', '-m', 'rsync', '-c', f'gs://{kw["bucket"]}/csv_output/{kw["collection"]}', os.path.join('output', kw["collection"])])
    ut.shell_exec(['gsutil', '-m', 'rsync', '-c', '-d', f'gs://{kw["bucket"]}/csv_output/{kw["collection"]}/backup', os.path.join('uploads', kw["collection"], 'backup')])
    if 'lmf' in kw["collection"]:
        for fil in os.listdir(os.path.join('output', kw["collection"])):
            if '.gpg' in fil:
                ut.shell_exec(['gpg', '-d', '-o', os.path.join('output', kw["collection"], fil.replace('.gpg', '')), os.path.join('output', kw["collection"], fil)])

def do_aggregate(static, **kw):
    print('Aggregate')
    agg_dl.full_aggregate(static=static, **kw)
    if 'lmf' in kw["collection"]:
        for fil in os.listdir(os.path.join('uploads', kw["collection"])):
            if '.csv' in fil:
                ut.shell_exec(['gpg', '-c', os.path.join('uploads', kw["collection"], fil)])

def do_upload(**kw):
    print('Upload')
    ut.shell_exec(['gsutil', '-m', 'rsync', '-c', os.path.join('uploads', kw["collection"]), f'gs://{kw["bucket"]}/csv_output/{kw["collection"]}'])
    ut.shell_exec(['gsutil', '-m', 'rsync', '-c', '-d', os.path.join('uploads', kw["collection"], 'backup'), f'gs://{kw["bucket"]}/csv_output/{kw["collection"]}/backup'])

def clean_bucket_duplicates(**kw):
    print('Clean Bucket_Duplicates')
    bucket_files = ut.shell_exec(['gsutil', 'ls', f'gs://{kw["bucket"]}/csv_output/{kw["collection"]}/*.csv'], my_out=True)[0].decode('utf-8').split('\n')[:-1]
    bucket_backup_files = ut.shell_exec(['gsutil', 'ls', f'gs://{kw["bucket"]}/csv_output/{kw["collection"]}/backup/*.csv'], my_out=True)[0].decode('utf-8').split('\n')[:-1]
    for fil in bucket_files:
        if os.path.basename(fil) in [os.path.basename(fl) for fl in bucket_backup_files]:
            ut.shell_exec(['gsutil', 'rm', fil])

def clean_up(**kw):
    print('Clean Up')
    ut.shell_exec(['gsutil', '-m', 'rm', f'gs://{kw["bucket"]}/*.csv'])
    clean_bucket_duplicates(**kw)
    clean.main(kw["collection"])

def full_static_run(**kw):
    ### Init
    kw = init(**kw)
    if not kw:
        return
    ### Make yamls
    make_yamls(**kw)
    ### Get list of files from server
    get_cloud_files(**kw)
    ### Submit jobs to generate Earth Engine csvs and put on server, check if finished, download, and remove from server, parse and remove downloaded files
    job_success = submit_jobs_static(**kw)
    if not job_success:
        print('No files have been processed, exiting...')
        ut.remove('cloud_files')
    else:
        ### Download previously downloaded files (if not available locally)
        do_rsync_down(**kw)
        ### Aggregate all files in preparation for upload to server
        do_aggregate(static='static', **kw)
        ### Upload csvs and clear directory
        do_upload(**kw)
        ### Clean up temporary generated files
        clean_up(**kw)
    return kw

def full_run(**kw):
    ### Init
    kw = init(**kw)
    if not kw:
        return
    ### Make yamls
    make_yamls(**kw)
    ### Warn for incorrent provided vars
    bad_vars = warn_provided_vars(**kw)
    if bad_vars:
        print('WARNING: The following variables could not be located in the config files:')
        print(bad_vars)
        print('Please ensure that all variables are spelled correctly.')
        print('If these are typos, the variables to which they correspond will not be processed until the typos are corrected in run_parameters!')
    ### Get list of files from server
    get_cloud_files(**kw)
    ### Get dates from list of cloud files
    kw = do_dates(**kw)
    ### Submit jobs to generate Earth Engine csvs and put on server, check if finished, download, and remove from server, parse and remove downloaded files
    job_success = submit_jobs(**kw)
    if not job_success:
        print('No dynamic files have been processed, exiting...')
        ut.remove('cloud_files')
    else:
        ### Download previously downloaded files (if not available locally)
        do_rsync_down(**kw)
        ### Aggregate all files in preparation for upload to server
        do_aggregate(static='dynamic', **kw)
        ### Upload csvs and clear directory
        do_upload(**kw)
        ### Clean up temporary generated files
        clean_up(**kw)
        ### Create visualization html
        ut.remove(os.path.join('output', f'{kw["collection"]}_report.html'))
        tabs = dataviz.generate_visualization(wd='output', collection=kw['collection'])
        show(tabs)
    return kw

