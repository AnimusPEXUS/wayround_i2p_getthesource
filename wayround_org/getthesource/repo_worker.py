
import os.path
import subprocess
import random

import wayround_org.utils.path


def work_on_source_repository(path):

    ret = 0

    path = wayround_org.utils.path.abspath(path)

    print("work_on_source_repository at: {}".format(path))

    print("getting file list")

    lst = os.listdir(path)

    lst_files = []

    print("unlisting normal files")
    for i in range(len(lst) - 1, -1, -1):
        j = wayround_org.utils.path.join(path, lst[i])
        if not os.path.isdir(j):
            lst_files.append(lst[i])
            del lst[i]

    print("sorting list")
    lst.sort()
    lst_files.sort()
    lst_dirs = lst
    del lst

    print("searching tree, upp.py or upp.sh under: {}".format(path))
    if 'tree' in lst_files:
        print("   found tree")
        random.shuffle(lst_dirs)
        for i in lst_dirs:
            j = wayround_org.utils.path.join(path, i)
            print("   passing recursuin under: {}".format(j))
            work_on_source_repository(j)
            print("   recursion exited from: {}".format(j))
    elif 'upp.py' in lst_files:
        print("   found upp.py")
        file_ = wayround_org.utils.path.join(path, 'upp.py')
        p = subprocess.Popen(
            ['python3', file_],
            cwd=path
            )
        print("   ...waiting...")
        p_ret = p.wait()
        print("      {} exited with {}".format(file_, p_ret))
    elif 'upp.sh' in lst_files:
        print("   found upp.sh")
        file_ = wayround_org.utils.path.join(path, 'upp.sh')
        p = subprocess.Popen(
            ['bash', file_],
            cwd=path
            )
        print("   ...waiting...")
        p_ret = p.wait()
        print("      {} exited with {}".format(file_, p_ret))
    else:
        pass

    print("work_on_source_repository exiting from: {}".format(path))

    return ret
