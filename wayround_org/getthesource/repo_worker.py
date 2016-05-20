
import logging
import os.path
import subprocess
import random
import datetime
import yaml
import collections

import wayround_org.utils.path
import wayround_org.utils.datetime_iso8601


def work_on_source_repository(path):

    ret = 0

    path = wayround_org.utils.path.abspath(path)

    print("work_on_source_repository at: {}".format(path))

    start_stop_file_path = os.path.join(path, 'start_stop.yaml')

    old_enough = True

    if os.path.isfile(start_stop_file_path):
        with open(start_stop_file_path) as start_stop_file:
            start_stop_file_txt = start_stop_file.read()

        try:
            start_stop_file_data = yaml.load(start_stop_file_txt)
        except:
            logging.exception("error")

        else:

            if (isinstance(start_stop_file_data, list)
                and
                len(start_stop_file_data) == 2
                and
                isinstance(start_stop_file_data[1], dict)
                and
                start_stop_file_data[1]['action'] == 'end'
                and

                    (
                        (
                            (
                                datetime.datetime.utcnow()
                                -
                                wayround_org.utils.datetime_iso8601.from_str(
                                    start_stop_file_data[
                                        1]['datetime_UTC0']
                                )[0]
                            ) < datetime.timedelta(days=3)
                        )

                    and 'status' in start_stop_file_data[1]
                    and start_stop_file_data[1]['status'] == 0

                            )
                    ):
                old_enough = False

            del start_stop_file_data
            del start_stop_file_txt

    if not old_enough:
        print("not old enough")
        ret = 2

    else:

        start_stop_file = open(start_stop_file_path, 'w')

        start_stop_file.write(
            yaml.dump([
                collections.OrderedDict(
                    {
                        'action': 'begin',
                        'datetime_UTC0':
                        wayround_org.utils.datetime_iso8601.to_str(
                            datetime.datetime.utcnow()
                            )
                    }
                    )
                ])
            )

        start_stop_file.flush()

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
            f = open(
                os.path.join(
                    path,
                    'wrogts_tree_walking_status_log.txt'),
                'w')
            f.write(
                "this file is created at {}\n".format(
                    datetime.datetime.now()))
            f.write(" the path is {}\n".format(path))
            f.write(" (note: below count is starting from 1 (one))\n")
            f.write(" (note: datetime is local UTC time\n")
            f.flush()

            f.write(" order:\n")

            for i in lst_dirs:
                f.write(
                    " ({:>5}) {}\n".format(
                        str(lst_dirs.index(i) + 1),
                        i
                        )
                    )

            f.flush()

            for i in lst_dirs:
                f.write(
                    " ({:>5} of {:>5}) (time: {}) going to enter: {}\n".format(
                        str(lst_dirs.index(i) + 1),
                        str(len(lst_dirs)),
                        datetime.datetime.now(),
                        i
                        )
                    )
                f.flush()
                j = wayround_org.utils.path.join(path, i)
                print("   discending into: {}".format(j))
                work_on_source_repository(j)
                print("   recursion exited from: {}".format(j))
            f.write("closing file at {}\n".format(datetime.datetime.now()))
            f.close()
        elif 'upp.py' in lst_files:
            print("   starting upp.py")
            file_ = wayround_org.utils.path.join(path, 'upp.py')
            p = subprocess.Popen(
                ['python3', file_],
                cwd=path
                )
            print("   ...waiting...")
            p_ret = p.wait()
            print("      {} exited with {}".format(file_, p_ret))
        elif 'upp.sh' in lst_files:
            print("   starting upp.sh")
            file_ = wayround_org.utils.path.join(path, 'upp.sh')
            p = subprocess.Popen(
                ['bash', file_],
                cwd=path
                )
            print("   ...waiting...")
            p_ret = p.wait()
            print("      {} exited with {}".format(file_, p_ret))
        else:
            print("   nothing found")
            print("    exiting")

        start_stop_file.write(
            yaml.dump([
                collections.OrderedDict(
                    {
                        'action': 'end',
                        'datetime_UTC0':
                        wayround_org.utils.datetime_iso8601.to_str(
                            datetime.datetime.utcnow()
                            ),
                        'status': ret
                    }
                    )
                ])
            )

        start_stop_file.close()

    print("work_on_source_repository exiting from: {}".format(path))

    return ret
