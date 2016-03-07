
import collections
import yaml
import pprint
import logging

import wayround_org.utils.getopt
import wayround_org.utils.text

import wayround_org.getthesource.controller

CONFIG_PATH = '/etc/wrogts.conf.yaml'


def commands():
    ret = collections.OrderedDict([
        #('print-provider-info', providers_print_info),
        ('list-providers', providers_list),
        ('list-projects', provider_projects_list),
        ('list-tarballs', tarball_list)
        #('find-tarball-uris', find_tarball_uris)
    ])
    return ret


def load_config(path):
    ret = None
    try:
        with open(path) as f:
            ret = yaml.load(f.read())
    except:
        logging.exception("error while loading config: {}".format(path))
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
        controller = wayround_org.getthesource.controller.Controller(cfg)
        res = controller.list_providers()

        print("count: {}".format(len(res)))
        print(wayround_org.utils.text.return_columned_list(res), end='')
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

        controller = wayround_org.getthesource.controller.Controller(cfg)
        res = controller.list_projects(provider)

        if res is None:
            logging.error(
                "error getting list of rojects for `{}'".format(provider)
                )
            ret = 5
        else:
            print("count: {}".format(len(res)))
            print(wayround_org.utils.text.return_columned_list(res), end='')
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

        controller = wayround_org.getthesource.controller.Controller(cfg)
        res = controller.list_tarballs(provider, project)

        if res is None:
            logging.error("error getting list of tarballs for")
            ret = 5
        else:
            for i in res.keys():

                print("{}".format(i))

                for j in res[i].keys():
                    print ("    {}".format(j))
                    
                    lst = []
                    for k in range(len(res[i][j])):
                        lst.append(res[i][j][k])

                    lst.sort(key=lambda x: x[0]) # , reverse=True

                    for k in lst:
                        print("        {}:\n            {}\n".format(k[0], k[1]))

    return ret
