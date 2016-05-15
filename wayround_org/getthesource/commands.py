
import os.path
import collections
import yaml
import pprint
import logging
import regex
import datetime

import wayround_org.utils.getopt
import wayround_org.utils.text
import wayround_org.utils.path

import wayround_org.getthesource.uriexplorer
import wayround_org.getthesource.mirrorer
import wayround_org.getthesource.git_tool
import wayround_org.getthesource.repo_worker


CONFIG_PATH = '/etc/wrogts.conf.yaml'


def commands():
    ret = collections.OrderedDict([
        #('print-provider-info', providers_print_info),
        ('list-providers', providers_list),
        ('list-projects', provider_projects_list),
        ('list-tarballs', tarball_list),
        ('list-basenames', basename_list),
        #('find-tarball-uris', find_tarball_uris)
        ('run-mirroring', mirrorer_work_on_dir),
        ('simple', simple_mirroring),
        ('mirror-github', mirror_github),
        ('mirror-gitlab', mirror_gitlab),
        ('mirror-git', mirror_git),
        ('work-on-repo', repo_do_work)
    ])
    return ret


def load_config(path):
    ret = None
    try:
        with open(path) as f:
            ret = yaml.load(f.read())
    except:
        logging.exception("error while loading config: {}".format(path))

    if ret is None:
        ret = {}

    return ret


def interprete_provider_param_value(value):
    if value is None:
        pass
    else:
        value = value.split(',')
        if len(value) == 0:
            value = []
    return value


def interprete_project_param_value(value):
    return interprete_provider_param_value(value)


def providers_list(command_name, opts, args, adds):
    ret = 0
    cfg = load_config(CONFIG_PATH)

    if cfg is None:
        ret = 2

    if ret == 0:
        controller = wayround_org.getthesource.uriexplorer.URIExplorer(cfg)
        res = controller.list_providers()

        print("count: {}".format(len(res)))
        print(
            wayround_org.utils.text.return_columned_list(
                res,
                width=80
                ),
            end=''
            )
        print("count: {}".format(len(res)))

    return ret


def provider_projects_list(command_name, opts, args, adds):
    ret = 0
    cfg = load_config(CONFIG_PATH)

    if cfg is None:
        ret = 2

    if len(args) != 1:
        logging.error(
            "this command requires single argument - the provider name"
            )
        ret = 3

    if ret == 0:
        provider = interprete_provider_param_value(args[0])

    if ret == 0:

        if len(provider) != 1:
            logging.error("exactly one provider must be named")
            ret = 4

    if ret == 0:

        provider = provider[0]

        controller = wayround_org.getthesource.uriexplorer.URIExplorer(cfg)
        res = controller.list_projects(provider)

        if res is None:
            logging.error(
                "error getting list of rojects for `{}'".format(provider)
                )
            ret = 5
        else:
            print("count: {}".format(len(res)))
            print(
                wayround_org.utils.text.return_columned_list(
                    res,
                    width=80
                    ),
                end=''
                )
            print("count: {}".format(len(res)))

    return ret


def tarball_list(command_name, opts, args, adds):
    ret = 0
    cfg = load_config(CONFIG_PATH)

    if cfg is None:
        ret = 2

    ret = wayround_org.utils.getopt.check_options(
        opts,
        [
            '--provider=', '-P=',
            '--project=', '-p='
            ]
        )

    if ret == 0:

        provider = opts.get('-P')
        if provider is None:
            provider = opts.get('--provider')

        project = opts.get('-p')
        if project is None:
            project = opts.get('--project')

        provider = interprete_provider_param_value(provider)
        project = interprete_project_param_value(project)

    if ret == 0:

        controller = wayround_org.getthesource.uriexplorer.URIExplorer(cfg)
        res = controller.list_tarballs(provider, project)

        if res is None:
            logging.error("error getting list of tarballs for")
            ret = 5
        else:
            for i in sorted(list(res.keys())):

                print("{}".format(i))

                for j in sorted(list(res[i].keys())):
                    print("    {}".format(j))

                    lst = []
                    for k in range(len(res[i][j])):
                        lst.append(res[i][j][k])

                    lst.sort(key=lambda x: x[0])  # , reverse=True

                    for k in lst:
                        print(
                            "        {}:\n            {}\n".format(k[0], k[1])
                            )
                    print("        " + '-' * 70)

    return ret


def basename_list(command_name, opts, args, adds):
    ret = 0
    cfg = load_config(CONFIG_PATH)

    if cfg is None:
        ret = 2

    ret = wayround_org.utils.getopt.check_options(
        opts,
        [
            '--provider=', '-P=',
            '--project=', '-p='
            ]
        )

    if ret == 0:

        provider = opts.get('-P')
        if provider is None:
            provider = opts.get('--provider')

        project = opts.get('-p')
        if project is None:
            project = opts.get('--project')

        provider = interprete_provider_param_value(provider)
        project = interprete_project_param_value(project)

    if ret == 0:

        controller = wayround_org.getthesource.uriexplorer.URIExplorer(cfg)
        res = controller.list_basenames(provider, project)

        if res is None:
            logging.error("error getting list of tarballs for")
            ret = 5
        else:
            for i in sorted(list(res.keys())):

                print("{}".format(i))

                for j in sorted(list(res[i].keys())):
                    print("    {}".format(j))
                    print(
                        wayround_org.utils.text.return_columned_list(
                            sorted(res[i][j]),
                            margin_left='        | ',
                            width=80
                            ),
                        end=''
                        )
                    print("        " + '-' * 70)

    return ret


def mirrorer_work_on_dir(command_name, opts, args, adds):
    """
    DIRNAME - single required argument

        -mc=path - use specified mirroring config file instead of
            wrogts_mirrorer.conf.yaml under DIRNAME
    """
    ret = 0
    cfg = load_config(CONFIG_PATH)

    if cfg is None:
        ret = 2

    if len(args) != 1:
        logging.error(
            "this command requires single argument - "
            "directory in which to run"
            )
        ret = 3

    if ret == 0:
        working_directory = args[0]

    if ret == 0:

        if 'general' not in cfg:
            cfg['general'] = {}

        cfg['general']['log_dir'] = wayround_org.utils.path.join(
            working_directory,
            'wrogts-logs'
            )

        cfg['general']['cache_dir'] = wayround_org.utils.path.join(
            working_directory,
            'wrogts-cache'
            )

        mirrorer_cfg = None

        if '-mc' in opts:
            with open(opts['-mc']) as f:
                mirrorer_cfg = yaml.load(f.read())

        uriexplorer = wayround_org.getthesource.uriexplorer.URIExplorer(cfg)
        mirrorer = wayround_org.getthesource.mirrorer.Mirrorer(
            cfg,
            working_directory,
            uriexplorer
            )
        ret = mirrorer.work_on_dir(mirrorer_cfg)

    return ret


def value_split_by_sign(value, sign=','):
    ret = value
    if isinstance(ret, str):
        ret = ret.split(sign)
    return ret


def simple_mirroring(command_name, opts, args, adds):
    """
    Do simple mirroring of HTTPS directory tree into output dir.

    This command does not use config files. It's simply scans server's
    dirs for files and downloads tarballs into separate (by basename) dirs.

    SYNOPSIS
        simple
            [-mc=path]
            [-X=filters]
            [-XB=filters]
            [-R=filters]
            [-XR=filters]
            [-XBR=filters]
            [-RR=filters]
            [-TBW=filters]
            URI [WORKDIRNAME]

        if WORKDIRNAME is not passed, current dir is used

    OPTIONS

        -X=COMMA_SEPARATED_LIST
            exclude paths

        -XB=COMMA_SEPARATED_LIST
            like -X, but works only on basenames of paths

        -R=COMMA_SEPARATED_LIST
            reject files

        -XR=COMMA_SEPARATED_LIST
            same as -X, but uses regex module

        -XBR=COMMA_SEPARATED_LIST
            same as -XB, but uses regex module

        -RR=COMMA_SEPARATED_LIST
            same as -R, but uses regex module

        -TBW=COMMA_SEPARATED_LIST
            white list for tarball basenames

        -mc=path - use specified mirroring config file instead of
            wrogts_mirrorer.conf.yaml under WORKDIRNAME

    """

    # print("args: {}".format(args))
    # print("opts: {}".format(opts))

    cfg = load_config(CONFIG_PATH)
    ret = 0

    if cfg is None:
        ret = 2

    if ret == 0:
        if len(args) == 0:
            logging.error("URI - is necessary argument")
            ret = 3

    if ret == 0:

        if len(args) > 0:
            uri = args[0]

    if ret == 0:
        if len(args) == 2:
            working_directory = args[1]
        else:
            working_directory = os.getcwd()

        working_directory = wayround_org.utils.path.abspath(working_directory)

    if ret == 0:
        if len(args) > 2:
            logging.error("too many arguments")
            ret = 4

    if ret == 0:

        exclude_paths = value_split_by_sign(opts.get('-X', []))
        exclude_paths_bases = value_split_by_sign(opts.get('-XB', []))
        reject_files = value_split_by_sign(opts.get('-R', []))

        exclude_paths_re = value_split_by_sign(opts.get('-XR', []))
        exclude_paths_bases_re = value_split_by_sign(opts.get('-XBR', []))
        reject_files_re = value_split_by_sign(opts.get('-RR', []))

        tarball_basenames_whitelist = value_split_by_sign(
            opts.get('-TBW', None)
            )

        if 'general' not in cfg:
            cfg['general'] = {}

        cfg['general']['log_dir'] = wayround_org.utils.path.join(
            working_directory,
            'wrogts-logs'
            )

        cfg['general']['cache_dir'] = wayround_org.utils.path.join(
            working_directory,
            'wrogts-cache'
            )

        simple_config = {
            'exclude_paths': exclude_paths,
            'exclude_paths_bases': exclude_paths_bases,
            'reject_files': reject_files,

            'exclude_paths_re': exclude_paths_re,
            'exclude_paths_bases_re': exclude_paths_bases_re,
            'reject_files_re': reject_files_re,

            'target_uri': uri,
            'tarball_basenames_whitelist': tarball_basenames_whitelist
            }

        mirrorer_cfg = None

        if '-mc' in opts:
            with open(opts['-mc']) as f:
                mirrorer_cfg = yaml.load(f.read())

        working_directory = os.path.abspath(working_directory)

        os.makedirs(working_directory, exist_ok=True)

        uriexplorer = wayround_org.getthesource.uriexplorer.URIExplorer(
            cfg,
            simple_config=simple_config
            )

        mirrorer = wayround_org.getthesource.mirrorer.Mirrorer(
            cfg,
            working_directory,
            uriexplorer,
            simple_config=simple_config
            )

        ret = mirrorer.work_on_dir(mirrorer_cfg)

    return ret


def mirror_github(command_name, opts, args, adds):
    """

    makes mirror of selected github projects. optionally careating archives.

    example of download_list.yaml:

    libgit2:
      libgit2:
        make-tarballs: [libgit2]

    another one example:

    xkbcommon:
      libxkbcommon:
        make-tarballs:
          - {basename: libxkbcommon, needed_tag_re_prefix_is: 'xkbcommon',
             needed_tag_re_suffix_is: '^$'}

    make-tarballs value is list of dicts:

        make-tarballs:
          - { # default values
              basename='v',                 # basename to use for naming
                                            # archives
              needed_tag_re_prefix_is='v',  # basename of tags which usable for
                                            # archiving
              needed_tag_re_suffix_is='^$', # same as needed_tag_re_prefix_is
                                            # but for suffix
              needed_tag_re=STD_TAG_RE,     # complete re to be used
              tarball_format='tar.xz',      # format for created archives
              truncate_versions=3           # version truncation number
            }
    """
    ret = 0

    working_dir = os.getcwd()
    if len(args) == 1:
        working_dir = args[0]

    working_dir = wayround_org.utils.path.abspath(working_dir)
    list_file_path = wayround_org.utils.path.join(
        working_dir,
        'download_list.yaml'
        )

    wayround_org.getthesource.git_tool.work_on_github_downloading_list(
        working_dir,
        list_file_path
        )

    return ret


def mirror_gitlab(command_name, opts, args, adds):
    ret = 0

    working_dir = os.getcwd()
    if len(args) == 1:
        working_dir = args[0]

    working_dir = wayround_org.utils.path.abspath(working_dir)
    list_file_path = wayround_org.utils.path.join(
        working_dir,
        'download_list.yaml'
        )

    wayround_org.getthesource.git_tool.work_on_gitlab_downloading_list(
        working_dir,
        list_file_path
        )

    return ret


def mirror_git(command_name, opts, args, adds):
    """
    config file should be named download_list.yaml and be of structure:
    list of 3-lists, where 1 item is git repo uri, 2 item output directory
    and 3 item is target downloading instructions, like in mirror-github cmd
    can be none

    see mirror-github help for description of third list item

    example:

    - - 'https://go.googlesource.com/go'
      - 'git'
      - {make-tarballs: [{basename: go, needed_tag_re_prefix_is: go}]}
    """
    ret = 0

    working_dir = os.getcwd()
    if len(args) == 1:
        working_dir = args[0]

    working_dir = wayround_org.utils.path.abspath(working_dir)
    list_file_path = wayround_org.utils.path.join(
        working_dir,
        'download_list.yaml'
        )

    log_file_path = wayround_org.utils.path.join(
        working_dir,
        'log.txt'
        )

    f = open(log_file_path, 'w')
    f.write("start: {}\n".format(datetime.datetime.now()))
    f.flush()

    wayround_org.getthesource.git_tool.work_on_git_downloading_list(
        working_dir,
        list_file_path
        )

    f.write("end: {}\n".format(datetime.datetime.now()))
    f.close()

    return ret


def repo_do_work(command_name, opts, args, adds):
    ret = 0
    path = os.path.abspath(os.getcwd())
    ret = wayround_org.getthesource.repo_worker.work_on_source_repository(path)
    return ret
