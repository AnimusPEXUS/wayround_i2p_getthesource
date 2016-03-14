
import os.path
import copy
import logging
import importlib
import datetime

import yaml

import wayround_org.utils.path
import wayround_org.utils.tarball
import wayround_org.utils.version

import wayround_org.getthesource.uriexplorer


class Mirrorer:

    def __init__(self, cfg, uriexplorer):

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
            'mirrorer {}'.format(datetime.datetime.utcnow())
            )

        if not isinstance(
                uriexplorer,
                wayround_org.getthesource.uriexplorer.URIExplorer
                ):
            raise TypeError(
                "`uriexplorer' must be inst of "
                "wayround_org.getthesource.uriexplorer.URIExplorer"
                )

        self.uriexplorer = uriexplorer

        self.downloaders = {}

        self._load_downloaders()

        return

    def _load_downloaders(self):
        """
        This method should be started only once - on object init
        """
        downloader_dir = wayround_org.utils.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'modules',
            'downloaders'
            )
        downloaders = []
        for i in sorted(os.listdir(downloader_dir)):
            if i.endswith('.py'):
                j = wayround_org.utils.path.join(
                    downloader_dir,
                    i
                    )
                if os.path.isfile(j):
                    downloaders.append(i[:-3])

        if '__init__' in downloaders:
            downloaders.remove('__init__')

        for i in downloaders:
            mod = importlib.import_module(
                'wayround_org.getthesource.modules.downloaders.{}'.format(i)
                )
            p = mod.Downloader(self)
            if p.get_is_downloader_enabled():
                self.downloaders[p.get_downloader_code_name()] = p
            del mod
            del p

        return

    def work_on_dir(self, path):

        ret = 0

        self.logger.info(
            "Got task to perform mirroring in dir: {}".format(path)
            )

        path = wayround_org.utils.path.abspath(path)

        m_cfg_path = wayround_org.utils.path.join(
            path,
            'wrogts_mirrorer.conf.yaml'
            )

        self.logger.info("loading config: {}".format(m_cfg_path))

        with open(m_cfg_path) as f:
            m_cfg = yaml.load(f.read())

        if not isinstance(m_cfg, list):
            self.logger.error(
                "invalid structure of {}".format(m_cfg_path)
                )
            ret = 1

        if ret == 0:
            self.logger.info(
                "mirroring config contains {} description(s)".format(
                    len(m_cfg)
                    )
                )
            for i in m_cfg:
                self.logger.info("------------------------")
                self.logger.info(
                    "processing description #{}".format(m_cfg.index(i))
                    )
                options = {
                    'preferred_tarball_compressors': (
                        wayround_org.utils.tarball.
                        ACCEPTABLE_SOURCE_NAME_EXTENSIONS
                        ),
                    'only_latests': 3,
                    'ignore_invalid_connection_security': False,

                    # NOTE: using and enabling this may be unsafe
                    'delete_old_tarballs': False,

                    'downloader_obfuscation_required': False
                    }

                if 'options' in i:
                    for j in options.keys():
                        if j in i['options']:
                            options[j] = i['options'].get(j, None)

                targets = i.get('targets', {})

                self.work_on_dir_with_settings(
                    path,
                    {
                        'options': options,
                        'targets': targets
                        }
                    )

        return ret

    def work_on_dir_with_settings(self, path, settings):
        """
        settings['targets'] structure:
        {
            # if value to key is dict, then assume project devision of provider.
            # else, if list, assume list of tarball basenames to get.
            # if value is None - get all project names from provider and get all
            # bases from them.
            'gnu.org': {
                'gcc': [  # list of tarball basenames to get. if None - get all
                          # bases provided by project
                    'gcc'
                ]
            }
        }
        """

        ret = 0

        settings_targets = settings.get('targets', {})
        settings_options = settings.get('options', {})

        #print("settings_targets: {}".format(settings_targets))
        #print("settings_options: {}".format(settings_options))

        requested_provider_names = list(settings_targets.keys())

        requested_provider_names.sort()

        for provider_name in requested_provider_names:
            if provider_name not in self.uriexplorer.list_providers():
                self.logger.error(
                    "No requested provider named: {}".format(provider_name)
                    )
                continue

            provider = self.uriexplorer.providers[provider_name]
            provider_has_projects = provider.get_project_param_used()
            provider_project_names = None
            if provider_has_projects:
                provider_project_names = provider.get_project_names()

            provider_target_setting = settings_targets[provider_name]

            if provider_target_setting is None:

                if provider_has_projects:
                    for i in provider_project_names:
                        for j in provider.basenames(i):
                            self.work_on_dir_with_basename(
                                path,
                                provider_name,
                                i,
                                j,
                                settings_options
                                )
                else:
                    for i in provider.basenames():
                        self.work_on_dir_with_basename(
                            path,
                            provider_name,
                            None,
                            i,
                            settings_options
                            )

            elif isinstance(provider_target_setting, list):
                if not provider_has_projects:
                    self.logger.error(
                        "setting for `{}' excludes projects subdivision, but "
                        "this provider is subdivided on projects"
                        "".format(provider_name)
                        )
                    continue

                for i in provider_target_setting:
                    if i not in provider_project_names:
                        self.logger.error(
                            "provider `{}' has no project `{}'".format(
                                provider_name,
                                i
                                )
                            )
                        continue

                    for j in provider.basenames(i):
                        self.work_on_dir_with_basename(
                            path,
                            provider_name,
                            i,
                            j,
                            settings_options
                            )
            elif isinstance(provider_target_setting, dict):

                if not provider_has_projects:
                    self.logger.error(
                        "setting for `{}' means projects, but this provider"
                        " isn't subdivided onto projects".format(provider_name)
                        )
                    continue

                for i in sorted(list(provider_target_setting.keys())):
                    for j in sorted(list(provider_target_setting[i].keys())):

                        if i not in provider_project_names:
                            self.logger.error(
                                "provider `{}' has no project `{}'".format(
                                    provider_name,
                                    i
                                    )
                                )
                            continue

                        provider_project_basenames = provider.basenames(j)

                        basenames = provider_target_setting[i][j]
                        if basenames is None:
                            basenames = provider_project_basenames

                        for k in basenames:

                            if k not in provider_project_basenames:
                                self.logger.error(
                                    "provider `{}' project `'{}"
                                    " has no basename `{}'".format(
                                        provider_name,
                                        j,
                                        k,
                                        )
                                    )
                                continue

                            self.work_on_dir_with_basename(
                                path,
                                provider_name,
                                i,
                                j,
                                settings_options
                                )
            else:
                self.logger.error(
                    "invalid type of target description"
                    " structure for provider:"
                    " {}".format(provider_name)
                    )
                errors_oqcured = True

        return ret

    def work_on_dir_with_basename(
            self,
            path,
            provider,
            project,
            basename,
            options
            ):
        path = wayround_org.utils.path.abspath(path)

        project_path_part = []
        if project is not None:
            project_path_part.append(project)

        output_path = wayround_org.utils.path.join(
            path,
            'downloads',
            provider,
            project_path_part,
            basename
            )

        os.makedirs(output_path, exist_ok=True)

        tarballs = self.uriexplorer.list_tarballs(provider, project)

        needed_tarballs = []

        for i in tarballs:
            parse_result = wayround_org.utils.tarball.parse_tarball_name(i[0])
            if parse_result is None:
                continue
            if parse_result['groups']['name'] == basename:
                needed_tarballs.append(i)

        del tarballs

        only_latests = options.get('only_latests', 3)

        if isinstance(only_latests, int):

            filter_for_latests_res = []

            bases = []

            for i in only_latests:
                bases.append(i[0])

            wayround_org.utils.version.remove_invalid_bases(bases)

            tree = wayround_org.utils.version.same_base_structurize_by_version(
                bases
                )

            wayround_org.utils.version.truncate_ver_tree(tree, only_latests)

            bases = wayround_org.utils.version.get_bases_from_ver_tree(
                tree,
                options['preferred_tarball_compressors']
                )

            tarballs_to_download = []
            for i in bases:
                for j in needed_tarballs:
                    if j[0].endswith('/' + i) or j[0] == i:
                        tarballs_to_download.append(i)

            tarballs_to_delete = []
            for i in os.listdir(output_path):
                ij = wayround_org.utils.path.join(
                    output_path,
                    i
                    )

                if os.path.isfile(ij):
                    if i not in bases:
                        tarballs_to_delete.append(i)

            # TODO: here must be something smarter, but I'm in horry
            downloader = self.downloaders['wget']
            for i in tarballs_to_download:
                downloader.download(
                    i[1],
                    output_path,
                    new_basename=os.path.basename(i[0]),
                    stop_event=None,
                    ignore_invalid_connection_security=(
                        options['ignore_invalid_connection_security']
                        ),
                    downloader_obfuscation_required=(
                        options['downloader_obfuscation_required']
                        )
                    )

        return
