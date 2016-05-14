
import subprocess
import os.path
import re
import yaml
import random

import wayround_org.utils.path
import wayround_org.utils.file
import wayround_org.utils.version


STD_TAG_RE = (
    r'^'
    r'((?P<prefix>.*?)[\-\_]?)?'
    r'(?P<version>\d+(?P<delim>[\_\-\.])(\d+(?P=delim)?)*)'
    r'([\-\_]??(?P<suffix>.*?)??)??'
    r'$'
    )
#STD_TAG_RE_C = re.compile(STD_TAG_RE)


def clone_and_update(
        git_uri,
        output_dir,
        no_check_certificate=False
        ):

    ret = 0

    output_dir = wayround_org.utils.path.abspath(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    if wayround_org.utils.file.isdirempty(output_dir):
        p = subprocess.Popen(
            ['git', 'clone', git_uri, output_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
            )
        ret = p.wait()
    else:
        p = subprocess.Popen(
            ['git', 'pull'],
            cwd=output_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
            )
        ret = p.wait()

    return ret


def get_tags(git_dir):
    p = subprocess.Popen(
        ['git', 'tag'],
        cwd=git_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
        )
    tags_txt = p.communicate()[0].decode('utf-8')
    tags_txt = tags_txt.strip()
    ret = tags_txt.split('\n')
    return ret


def archive(git_dir, tag, output_filename, prefix):
    ret = 0
    sum_file_name = output_filename + '.sha512'
    do_write = False
    if not os.path.isfile(sum_file_name):
        do_write = True
    else:

        with open(sum_file_name) as f:
            summ = f.read().strip()

        if summ.lower() != wayround_org.utils.checksum.make_file_checksum(
                output_filename,
                'sha512'
                ).lower():
            do_write = True

    if do_write:

        print(
            "  archive: `{}' -> {}".format(
                tag,
                os.path.basename(output_filename)
                )
            )

        cmd = ['git',
               'archive',
               '--prefix={}/'.format(prefix),
               '-o', output_filename,
               tag,
               ]

        p = subprocess.Popen(
            cmd,
            cwd=git_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
            )
        ret = p.wait()
        if ret == 0:
            with open(sum_file_name, 'w') as f:
                f.write(
                    wayround_org.utils.checksum.make_file_checksum(
                        output_filename,
                        'sha512'
                        ).lower()
                    )

    return ret


def make_tarballs(
        git_dir,
        output_dir,
        basename='v',
        needed_tag_re_prefix_is='v',
        needed_tag_re_suffix_is='^$',
        needed_tag_re=STD_TAG_RE,
        tarball_format='tar.xz',
        truncate_versions=3
        ):

    ret = 0

    output_dir = wayround_org.utils.path.abspath(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    tags = get_tags(git_dir)

    basename_str = basename

    # print("tags result for {} is: {}".format(git_dir, tags))

    acceptable_tags = {}

    for i in tags:
        re_res = re.match(needed_tag_re, i)
        if re_res is not None:
            prefix = re_res.group('prefix')
            version = re_res.group('version')
            delim = re_res.group('delim')
            suffix = re_res.group('suffix')

            if prefix is None:
                prefix = ''

            if suffix is None:
                suffix = ''

            if prefix is not None:
                prefix = prefix.strip('-._')

            if suffix is not None:
                suffix = suffix.strip('-._')

            '''
            print('i: {}'.format(i))

            print('re_res prefix: {}'.format(prefix))
            print('re_res version: {}'.format(version))
            print('re_res delim: {}'.format(delim))
            print('re_res suffix: {}'.format(suffix))
            print('-' * 20)
            '''
            if (
                (
                    prefix is not None
                    and re.match(needed_tag_re_prefix_is, prefix)
                    )
                and (
                    suffix is not None
                    and re.match(needed_tag_re_suffix_is, suffix)
                    )
                    ):

                version_str = version
                for j in ['-', '_']:
                    version_str = version_str.replace(j, '.')

                version_str = version_str.strip('-._')

                acceptable_tags[i] = {
                    'tag': i,
                    'prefix': prefix,
                    'suffix': suffix,
                    'version': version,
                    'version_str': version_str
                    }

    acceptable_tag_versions2 = []
    for i in list(acceptable_tags.keys()):
        acceptable_tag_versions2.append(
            'v{}.tar.xz'.format(acceptable_tags[i]['version_str'])
            )

    tree = wayround_org.utils.version.same_base_structurize_by_version(
        acceptable_tag_versions2
        )

    wayround_org.utils.version.truncate_ver_tree(tree, truncate_versions)

    acceptable_tag_versions2 = (
        wayround_org.utils.version.get_bases_from_ver_tree(
            tree,
            ['.tar.xz']
            )
        )

    for i in list(acceptable_tags.keys()):
        if (not 'v{}.tar.xz'.format(acceptable_tags[i]['version_str'])
                in acceptable_tag_versions2):
            del acceptable_tags[i]

    del acceptable_tag_versions2

    for i in reversed(sorted(list(acceptable_tags.keys()))):

        suffix_str = ''
        if len(acceptable_tags[i]['suffix']) != 0:
            suffix_str = '-{}'.format(acceptable_tags[i]['suffix'])

        basename_plus_version = '{}-{}{}'.format(
            basename_str,
            acceptable_tags[i]['version_str'],
            suffix_str
            )

        new_file_basename = '{}.{}'.format(
            basename_plus_version,
            tarball_format
            )

        output_filename = wayround_org.utils.path.join(
            output_dir,
            new_file_basename
            )

        archive(
            git_dir,
            i,
            output_filename,
            basename_plus_version
            )

    return ret


def work_on_github_downloading_list(
        work_dir,
        list_file_path,
        no_check_certificate=False,
        verbose=True
        ):
    list_file_path = wayround_org.utils.path.abspath(list_file_path)
    work_dir = wayround_org.utils.path.abspath(work_dir)

    with open(list_file_path) as f:
        targets = yaml.load(f.read())

    k1 = sorted(list(targets.keys()))
    random.shuffle(k1)
    for i in k1:
        for j in sorted(list(targets[i].keys())):
            if verbose:
                print("mirroring {}:{}".format(i, j))

            git_dir = wayround_org.utils.path.join(
                work_dir,
                i,
                j,
                'git'
                )
            tarballs_dir = wayround_org.utils.path.join(
                work_dir,
                i,
                j,
                'tarballs'
                )

            clone_and_update(
                'https://github.com/{}/{}.git'.format(i, j),
                git_dir,
                no_check_certificate=no_check_certificate
                )

            targets_i_j = targets[i][j]

            work_on_instructions(
                git_dir,
                tarballs_dir,
                targets_i_j,
                "{}:{}".format(i, j)
                )

    return


def work_on_gitlab_downloading_list(
        work_dir,
        list_file_path,
        no_check_certificate=False,
        verbose=True
        ):
    list_file_path = wayround_org.utils.path.abspath(list_file_path)
    work_dir = wayround_org.utils.path.abspath(work_dir)

    with open(list_file_path) as f:
        targets = yaml.load(f.read())

    k1 = sorted(list(targets.keys()))
    random.shuffle(k1)
    for i in k1:
        for j in sorted(list(targets[i].keys())):
            if verbose:
                print("mirroring {}:{}".format(i, j))

            git_dir = wayround_org.utils.path.join(
                work_dir,
                i,
                j,
                'git'
                )
            tarballs_dir = wayround_org.utils.path.join(
                work_dir,
                i,
                j,
                'tarballs'
                )

            clone_and_update(
                'https://gitlab.com/{}/{}.git'.format(i, j),
                git_dir,
                no_check_certificate=no_check_certificate
                )

            targets_i_j = targets[i][j]

            work_on_instructions(
                git_dir,
                tarballs_dir,
                targets_i_j,
                "{}:{}".format(i, j)
                )

    return


def work_on_git_downloading_list(
        work_dir,
        list_file_path,
        no_check_certificate=False
        ):
    list_file_path = wayround_org.utils.path.abspath(list_file_path)
    work_dir = wayround_org.utils.path.abspath(work_dir)

    with open(list_file_path) as f:
        targets = yaml.load(f.read())

    for i in targets:

        git_dir = wayround_org.utils.path.join(
            work_dir,
            i[1],
            'git'
            )

        tarballs_dir = wayround_org.utils.path.join(
            work_dir,
            i[1],
            'tarballs'
            )

        clone_and_update(
            i[0],
            git_dir,
            no_check_certificate=no_check_certificate
            )

        targets_i_2 = i[2]

        work_on_instructions(
            git_dir,
            tarballs_dir,
            targets_i_2,
            repr(i)
            )

    return


def work_on_instructions(
        git_dir,
        tarballs_dir,
        target_download_instructions,
        path_txt
        ):
    """
    ret: 0 - no errors, not 0 - was errors
    """

    ret = 0

    errors = False

    make_tarballs_instructions = target_download_instructions.get(
        'make-tarballs', []
        )

    if isinstance(make_tarballs_instructions, list):
        for i in make_tarballs_instructions:
            if isinstance(i, dict):
                make_tarballs(
                    git_dir,
                    tarballs_dir,
                    **i
                    )
            elif isinstance(i, str):
                make_tarballs(
                    git_dir,
                    tarballs_dir,
                    basename=i
                    )
            else:
                raise TypeError(
                    "invalid type of download descr at {}".format(path_txt)
                    )
    if errors:
        ret = 1

    return ret
