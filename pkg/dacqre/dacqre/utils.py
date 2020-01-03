import os
import subprocess
import contextlib


def remove(my_file):
    with contextlib.suppress(FileNotFoundError):
        os.remove(my_file)


def shell_pipe(com_list_list, my_sh=False):
    num_processes = len(com_list_list)
    process_list = []
    for idx, lst in enumerate(com_list_list):
        if idx == 0:
            process_list.append(subprocess.Popen(com_list_list[idx], stdout=subprocess.PIPE, shell=my_sh))
        else:
            process_list.append(subprocess.Popen(com_list_list[idx], stdin=process_list[idx-1].stdout, stdout=subprocess.PIPE, shell=my_sh))
        if idx > 0:
            process_list[idx-1].stdout.close()

    my_output  = process_list[num_processes-1].communicate()[0]
    del process_list, num_processes, my_output
    return

def shell_exec(com_list, my_sh=False, my_out=False):
    my_command = subprocess.Popen(com_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=my_sh)
    my_output  = my_command.communicate()
    if not my_out:
        del my_command, my_output
        return
    else:
        del my_command
        return my_output

def construct_docker_run(image: str, command: list=[], interactive: bool=True,
        remove: bool=True, name: str='', detached: bool=False, cwd: bool=True,
        workdir: bool=True, root: bool=True, env: list=[], volume: list=[]):
    run_list = ['docker', 'run']
    if interactive:
        run_list += ['-it']
    if remove:
        run_list += ['--rm']
    if detached:
        run_list += ['-d']
    if name:
        run_list += ['--name', name]
    if cwd:
        run_list += ['-v', f'{os.getcwd()}:/content']
    if workdir:
        run_list += ['-w', '/content']
    if not root:
        run_list += ['-u', f'{str(os.getuid())}:{str(os.getgid())}']
    for el in env:
        run_list += ['-e', el]
    for vol in volume:
        run_list += ['-v', vol]
    run_list += [image]
    for com in command:
        run_list += [com]
    return run_list

def shell_to_files(com_list, out_file, err_file, my_sh=False):
    with open(err_file, 'a+') as fh_e:
        with open(out_file, 'w') as fh_o:
            my_proc = subprocess.Popen(com_list, stdout=fh_o, stderr=fh_e, shell=my_sh)
    my_proc.communicate()
    del my_proc
    return
