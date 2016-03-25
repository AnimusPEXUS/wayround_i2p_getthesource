
import os.path
import subprocess

import wayround_org.utils.path


def work_on_source_repository(path):
    ret = 0

    path = wayround_org.utils.path.abspath(path)

    lst = os.listdir(path)
    lst_files = []

    for i in range(len(lst) - 1, -1, -1):
        j = wayround_org.utils.path.join(path, lst[i])
        if not os.path.isdir(j):
            lst_files.append(lst[i])
            del lst[i]

    lst.sort()
    lst_files.sort()
    lst_dirs = lst
    del lst

    if 'tree' in lst_files:
        for i in lst_dirs:
            j = wayround_org.utils.path.join(path, i)
            work_on_source_repository(j)
    elif 'upp.py' in lst_files:
        p = subprocess.Popen(
            wayround_org.utils.path.join(path, 'upp.py'), 
            cwd=path
            )
        p_ret = p.wait()
    elif 'upp.sh' in lst_files:
        p = subprocess.Popen(
            wayround_org.utils.path.join(path, 'upp.sh'), 
            cwd=path
            )
        p_ret = p.wait()
    else:
        pass

    return ret
