
import os.path
import importlib

import wayround_org.utils.path


class Controller:

    def __init__(self, cfg):
        self.cache_dir = '~/.config/wrogts/caches'
        try:
            self.cache_dir = cfg['general']['cache_dir']
        except:
            logging.exception(
                "Error getting ['general']['cache_dir'] value from config"
                )
            raise

        self.providers = {}

        self.cache_dir = os.path.expanduser(self.cache_dir)

        self._load_providers()

        return

    def _load_providers(self):
        """
        This method should be started only once - on object init
        """
        providers_dir = wayround_org.utils.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'modules',
            'providers'
            )
        providers = []
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
            if p.get_is_provider_enabled():
                self.providers[i] = p
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
        print("list_tarballs: {}, {}".format(providers, projects))
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

        '''
        for i in ret.keys():
            for j in ret[i].keys():
                ret[i][j].sort(key=lambda x: x[0], reverse=True)
        '''

        return ret

    def render_provider_info(self, provider_name):
        return

    def get_tarball_uris(self, basename, provider, project):
        """
        this method returns list with 2-tuples, where
            tuple[0] - is tarball base filename
            tuple[1] - complete url to get it

        basename - string - base name of tarballs to search for.
            for instance: 'wine', 'gcc', 'gcc-core', 'linux' etc.

        provider parameter can be None, string or list of strings, where
            None - means to try all providers GetTheSource knows of
            list - same as None, but try only listed providers
            string - treated as list of strings with single item

        project parameter can be None, string or list of strings:
            some providers can be additioanlly subdivided by projects, and
            can not be treeted as one pice. this is sf.net for instance,
            where only few projects of all resembles some usefull items. so in
            case of sf.net, project with value of None - means - get
            all usefull project names of sf.net and search for tarballs with
            basename among them, but is project name is string or list for
            strings, search only among listed projects

            None - search among all projects, all useful projects or among
                entire provider site, depending on nature of provider in
                question
            list - same as None, but try only listed projects
            string - treated as list of strings with single item
        """

        return
