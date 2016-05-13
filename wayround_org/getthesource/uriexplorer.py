
import os.path
import importlib
import logging
import datetime

import wayround_org.utils.path
import wayround_org.utils.log


class URIExplorer:

    def __init__(self, cfg, simple_config=None):

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

        self.providers = []

        self._load_providers_list(simple_mode=simple_config is not None)

        return

    def _load_providers_list(self, simple_mode=False):
        """
        This method should be started only once - on object init
        """
        providers_dir = wayround_org.utils.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'modules',
            'providers'
            )

        self.providers = []

        if simple_mode:
            self.providers.append('std_simple')
        else:
            for i in sorted(os.listdir(providers_dir)):
                if i.endswith('.py'):
                    j = wayround_org.utils.path.join(
                        providers_dir,
                        i
                        )
                    if os.path.isfile(j):
                        self.providers.append(i[:-3])

            if '__init__' in self.providers:
                self.providers.remove('__init__')

        return

    def get_provider(self, name):
        ret = None
        if name in self.providers:
            mod = importlib.import_module(
                'wayround_org.getthesource.modules.providers.{}'.format(name)
                )
            p = mod.Provider(self)
            if p.get_is_provider_enabled() or name == 'std_simple':
                ret = p

        return ret

    def list_providers(self):
        ret = sorted(list(self.providers))
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
        p = self.get_provider(provider)
        if p is not None and p.get_project_param_used():
            ret = p.get_project_names()
        return ret

    def _list_x(self, providers, projects, func_to_call):

        if func_to_call not in ['tarballs', 'basenames']:
            raise ValueError("error")

        ret = {}

        for i in sorted(list(self.providers)):

            if providers is None or i in providers:
                provider = self.get_provider(i)
                if provider.get_project_param_used():
                    for j in sorted(provider.get_project_names()):
                        if projects is None or j in projects:
                            for k in getattr(provider, func_to_call)(j):
                                if i not in ret:
                                    ret[i] = dict()
                                if j not in ret[i]:
                                    ret[i][j] = []
                                ret[i][j].append(k)
                else:
                    raise Exception("TODO")

        return ret

    def list_tarballs(self, providers, projects):
        return self._list_x(providers, projects, 'tarballs')

    def list_basenames(self, providers, projects):
        return self._list_x(providers, projects, 'basenames')

    def render_provider_info(self, provider_name):
        # TODO
        return
