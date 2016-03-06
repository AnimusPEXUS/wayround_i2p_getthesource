
import collections
import yaml
import pprint
import logging

import wayround_org.getthesource.controller

CONFIG_PATH = '/etc/wrogts.conf.yaml'


def commands():
    ret = collections.OrderedDict([
        #('print-provider-info', providers_print_info),
        ('list-providers', providers_list),
        ('list-projects', provider_projects_list),
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


def providers_list(command_name, opts, args, adds):
    ret = 0
    cfg = load_config(CONFIG_PATH)

    if cfg is None:
        ret = 2

    if ret == 0:
        controller = wayround_org.getthesource.controller.Controller(cfg)
        res = controller.list_providers()
        pprint.pprint(res)

    return ret


def provider_projects_list(command_name, opts, args, adds):
    ret = 0
    cfg = load_config(CONFIG_PATH)

    if cfg is None:
        ret = 2

    if len(args) != 1:
        logging.error(
            "this command requires single parameter - the provider name"
            )
        ret = 3

    if ret == 0:

        provider = args[0]

        controller = wayround_org.getthesource.controller.Controller(cfg)
        res = controller.list_projects(provider)
        pprint.pprint(res)

    return ret
