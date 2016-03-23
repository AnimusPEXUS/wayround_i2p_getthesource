
import os.path
import importlib
import logging
import datetime

import wayround_org.utils.path
import wayround_org.utils.log


class URIExplorer:

    def __init__(self, cfg, simple_mode=False, simple_config=None):

        log_dir = '~/.config/wrogts/logs'

        try:
            log_dir = cfg['general']['log_dir']
        except:
            logging.warning(
                "Error getting ['general']['log_dir'] value from config"
                )

        log_dir = os.path.expanduser(log_dir)

        self.logger = wayround_org.utils.log.Log(
            log_dir,
            'uriexplorer {}'.format(datetime.datetime.utcnow())
            )

        self.cache_dir = '~/.config/wrogts/caches'
        try:
            self.cache_dir = cfg['general']['cache_dir']
        except:
            self.logger.warning(
                "Error getting ['general']['cache_dir'] value from config"
                )

        self.cache_dir = os.path.expanduser(self.cache_dir)

        self.simple_config = simple_config

        self.providers = {}

        self._load_providers(simple_mode=simple_mode)

        return

    def _load_providers(self, simple_mode=False):
        """
        This method should be started only once - on object init
        """
        providers_dir = wayround_org.utils.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'modules',
            'providers'
            )

        providers = []

        if simple_mode:
            providers.append('std_simple')
        else:
            for i in sorted(os.listdir(providers_dir)):
                if i.endswith('.py'):
                    j = wayround_org.utils.path.join(
                        providers_dir,
                        i
                        )
                    if os.path.isfile(j):
                        providers.append(i[:-3])

            if '__init__' in providers:
                providers.remove('__init__')

        for i in providers:
            mod = importlib.import_module(
                'wayround_org.getthesource.modules.providers.{}'.format(i)
                )
            p = mod.Provider(self)
            if p.get_is_provider_enabled() or i == 'std_simple':
                self.providers[p.get_provider_code_name()] = p
            del mod
            del p

        return

    def list_providers(self):
        ret = sorted(list(self.providers.keys()))
        return ret

    def list_projects(self, provider):
        """
        return
            list of strings - names of projects provided by named provider.
            None - in case of error
            False - in case provider isn't devided on projects
        """

        if not isinstance(provider, str):
            raise TypeError("`provider' must be str")

        ret = None
        if provider in self.providers:
            p = self.providers[provider]
            ret = p.get_project_names()
        return ret

    def list_tarballs(self, providers, projects):
        ret = {}
        for i in sorted(list(self.providers.keys())):

            if providers is None or i in providers:
                provider = self.providers[i]
                if provider.get_project_param_used():
                    for j in sorted(provider.get_project_names()):
                        if projects is None or j in projects:
                            for k in provider.tarballs(j):
                                if not i in ret:
                                    ret[i] = dict()
                                if not j in ret[i]:
                                    ret[i][j] = []
                                ret[i][j].append(k)
                else:
                    raise Exception("TODO")

        return ret

    def list_basenames(self, providers, projects):
        ret = {}
        for i in sorted(list(self.providers.keys())):

            if providers is None or i in providers:
                provider = self.providers[i]
                if provider.get_project_param_used():
                    for j in sorted(provider.get_project_names()):
                        if projects is None or j in projects:
                            for k in provider.basenames(j):
                                if not i in ret:
                                    ret[i] = dict()
                                if not j in ret[i]:
                                    ret[i][j] = []
                                ret[i][j].append(k)
                else:
                    raise Exception("TODO")

        return ret

    def render_provider_info(self, provider_name):
        return
