
import os.path
import importlib

import yaml

import wayround_org.utils.path
import wayround_org.utils.tarball
import wayround_org.utils.version
import wayround_org.utils.checksum
import wayround_org.utils.uri

import wayround_org.getthesource.uriexplorer


class Mirrorer:

    def __init__(
            self,
            cfg,
            working_path,
            uriexplorer,
            simple_config=None
            ):

        working_path = wayround_org.utils.path.abspath(working_path)

        self.working_path = working_path

        self.logger = wayround_org.utils.log.Log(
            wayround_org.utils.path.join(self.working_path, 'logs'),
            'mirrorer'
            )

        if not isinstance(
                uriexplorer,
                wayround_org.getthesource.uriexplorer.URIExplorer
                ):
            raise TypeError(
                "`uriexplorer' must be inst of "
                "wayround_org.getthesource.uriexplorer.URIExplorer"
                )

        self.simple_config = simple_config

        self.uriexplorer = uriexplorer

        self.downloaders = []

        self._load_downloaders_list()

        return

    def _load_downloaders_list(self):
        """
        This method should be started only once - on object init
        """
        downloader_dir = wayround_org.utils.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'modules',
            'downloaders'
            )
        self.downloaders = []
        for i in sorted(os.listdir(downloader_dir)):
            if i.endswith('.py'):
                j = wayround_org.utils.path.join(
                    downloader_dir,
                    i
                    )
                if os.path.isfile(j):
                    self.downloaders.append(i[:-3])

        if '__init__' in self.downloaders:
            self.downloaders.remove('__init__')

        return

    def get_downloader(self, name):
        ret = None
        if name in self.downloaders:
            mod = importlib.import_module(
                'wayround_org.getthesource.modules.downloaders.{}'.format(name)
                )
            p = mod.Downloader(self)
            if p.get_is_downloader_enabled():
                ret = p

        return ret


    def work_on_dir(self, m_cfg=None):

        ret = 0

        path = self.working_path

        self.logger.info(
            "Got task to perform mirroring in dir: {}".format(path)
            )

        if m_cfg is None:

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
                self.logger.info('=' * 20)
                self.logger.info(
                    "processing description #{}".format(m_cfg.index(i))
                    )
                self.logger.info('-' * 20)
                options = {
                    'preferred_tarball_compressors': (
                        wayround_org.utils.tarball.
                        ACCEPTABLE_SOURCE_NAME_EXTENSIONS
                        ),
                    'only_latests': 3,
                    'ignore_invalid_connection_security': False,

                    # NOTE: using and enabling this may be unsafe
                    'delete_old_tarballs': False,

                    'downloader_obfuscation_required': False,
                    'redownload_prevention_checksum': 'sha512'
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

        self.logger.info(
            "{} provider name(s) in the list".format(
                len(requested_provider_names)
                )
            )
        self.logger.info('-' * 20)

        for provider_name in requested_provider_names:
            self.logger.info(
                "processing provider #{}: {}".format(
                    requested_provider_names.index(provider_name),
                    provider_name
                    )
                )
            self.logger.info('-' * 20)
            if provider_name not in self.uriexplorer.list_providers():
                self.logger.error(
                    "No requested provider named: {}".format(provider_name)
                    )
                continue

            provider = self.uriexplorer.get_provider(provider_name)
            provider_has_projects = provider.get_project_param_used()
            provider_project_names = None
            if provider_has_projects:
                provider_project_names = provider.get_project_names()

            provider_target_setting = settings_targets[provider_name]

            if provider_target_setting is None:

                self.logger.info("provider projects requested is None, so")

                if provider_has_projects:
                    self.logger.info(
                        "    getting list of names supplied by provider"
                        " and doing all basenames in them"
                        )
                    for i in provider_project_names:
                        basenames = provider.basenames(i)
                        for j in basenames:
                            self.logger.info(
                                "        project: {} ({} of {})"
                                " basename: {} ({} of {})".format(
                                    i,
                                    provider_project_names.index(i) + 1,
                                    len(provider_project_names),
                                    j,
                                    basenames.index(j) + 1,
                                    len(basenames)
                                    )
                                )
                            self.work_on_dir_with_basename(
                                path,
                                provider_name,
                                i,
                                j,
                                settings_options
                                )
                else:
                    basenames = None
                    self.logger.info(
                        "    getting list of basenames and doing them all"
                        )
                    if self.simple_config is not None:
                        if 'tarball_basenames_whitelist' in self.simple_config:
                            tbw = (
                                self.simple_config[
                                    'tarball_basenames_whitelist'
                                    ]
                                )
                            if isinstance(tbw, list):
                                self.logger.info(
                                    "        but whitelist is provided"
                                    " - using it!"
                                    )

                            basenames = tbw

                    if basenames is None:
                        basenames = provider.basenames(None)

                    for i in sorted(basenames):
                        self.work_on_dir_with_basename(
                            path,
                            provider_name,
                            None,
                            i,
                            settings_options
                            )

            elif isinstance(provider_target_setting, list):

                self.logger.info(
                    "provider projects requested is list so"
                    " assuming no project division"
                    )

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

                    basenames = provider.basenames(i)

                    for j in basenames:
                        self.logger.info(
                            "    project: {} ({} of {})"
                            " basename: {} ({} of {})".format(
                                i,
                                provider_target_setting.index(i) + 1,
                                len(provider_target_setting),
                                j,
                                basenames.index(j) + 1,
                                len(basenames)
                                )
                            )
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

                provider_target_setting_keys = sorted(
                    list(provider_target_setting.keys())
                    )

                for i in provider_target_setting_keys:
                    provider_target_setting_i_keys = sorted(
                        list(provider_target_setting[i].keys())
                        )
                    for j in provider_target_setting_i_keys:

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

                            self.logger.info(
                                "    project: {} ({} of {})"
                                " basename: {} ({} of {})".format(
                                    i,
                                    provider_target_setting_keys.index(i) + 1,
                                    len(provider_target_setting_keys),
                                    j,
                                    provider_target_setting_i_keys.index(
                                        j) + 1,
                                    len(provider_target_setting_i_keys)
                                    )
                                )

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

        self.logger.info('-' * 20)

        return ret

    def work_on_dir_with_basename(
            self,
            path,
            provider,
            project,
            basename,
            options
            ):

        self.logger.info(
            "task: {}, {}, {}".format(provider, project, basename)
            )

        path = wayround_org.utils.path.abspath(path)

        provired_obj = self.uriexplorer.get_provider(provider)

        project_path_part = []
        if project is not None:
            project_path_part.append(project)

        if provider != 'std_simple':
            output_path = wayround_org.utils.path.join(
                path,
                'downloads',
                provider,
                project_path_part,
                basename
                )
        else:
            output_path = wayround_org.utils.path.join(
                path,
                'downloads',
                # provider,
                project_path_part,
                basename
                )

        self.logger.info("  output dir going to be: {}".format(output_path))

        os.makedirs(output_path, exist_ok=True)

        self.logger.info(
            "  getting list of tarballs for `{}:{}'".format(provider, project)
            )
        tarballs = provired_obj.tarballs(project)  # [provider][]
        self.logger.info("    got {} item(s)".format(len(tarballs)))

        needed_tarballs = []

        self.logger.info(
            "  filtering tarballs list for `{}' basename".format(basename)
            )

        for i in tarballs:
            parse_result = wayround_org.utils.tarball.parse_tarball_name(i[0])
            if parse_result is None:
                continue
            if parse_result['groups']['name'] == basename:
                needed_tarballs.append(i)

        self.logger.info("    got {} item(s)".format(len(needed_tarballs)))

        del tarballs

        only_latests = options.get('only_latests', 3)

        if isinstance(only_latests, int):

            self.logger.info(
                "  truncating up to {} is requested".format(only_latests)
                )

            filter_for_latests_res = []

            bases = []

            for i in needed_tarballs:
                bases.append(os.path.basename(i[0]))

            bases = wayround_org.utils.tarball.remove_invalid_tarball_names(
                bases
                )

            tree = wayround_org.utils.version.same_base_structurize_by_version(
                bases
                )

            wayround_org.utils.version.truncate_ver_tree(tree, only_latests)

            # self.logger.info(
            #     "    before bases from tree: {}".format(len(bases))
            #     )
            bases = wayround_org.utils.version.get_bases_from_ver_tree(
                tree,
                options['preferred_tarball_compressors']
                )
            # self.logger.info(
            #     "    after bases from tree: {}".format(len(bases))
            #     )

            self.logger.info("    got {} item(s)".format(len(bases)))

            tarballs_to_download = []
            for i in bases:
                # print('i: {}'.format(i))
                for j in needed_tarballs:
                    # print('j[0]: {}'.format(j[0]))
                    if j[0].endswith('/' + i):
                        tarballs_to_download.append(j)

            tarballs_to_delete = []
            for i in os.listdir(output_path):
                j_found = False
                for j in (
                        wayround_org.utils.tarball.KNOWN_SIGNING_EXTENSIONS
                        + ['.sha1', '.sha512', '.sha224', '.sha256', '.sha384'
                            '.md5'
                           ]
                        ):
                    if i.endswith(j):
                        j_found = True
                        break
                if j_found:
                    continue

                ij = wayround_org.utils.path.join(output_path, i)

                if os.path.isfile(ij):
                    # print("is i in bases?: {}, {}, {}".format(i in bases, i, bases))
                    if i not in bases:
                        tarballs_to_delete.append(i)

            self.logger.info(
                "  {} file(s) is marked for download: {}".format(
                    len(tarballs_to_download),
                    [os.path.basename(i[0]) for i in tarballs_to_download]
                    )
                )

            self.logger.info(
                "  {} file(s) is marked as truncated"
                " (and will be deleted) (deletion is disabled for bugs): {}".format(
                    len(tarballs_to_delete),
                    tarballs_to_delete
                    )
                )

            # print("tarballs_to_download: {}".format(tarballs_to_download))

            # TODO: here must be something smarter, but I'm in horry
            downloader = self.get_downloader('wget')
            for i in tarballs_to_download:
                new_basename = os.path.basename(i[0])
                new_basename_full = wayround_org.utils.path.join(
                    output_path,
                    new_basename
                    )
                new_basename_full_cs = '{}.{}'.format(
                    new_basename_full,
                    options['redownload_prevention_checksum']
                    )
                actual_cs = None
                saved_cs = None

                if os.path.isfile(new_basename_full):
                    actual_cs = wayround_org.utils.checksum.make_file_checksum(
                        new_basename_full,
                        options['redownload_prevention_checksum']
                        )
                    if isinstance(actual_cs, str):
                        actual_cs = actual_cs.lower()
                        if os.path.isfile(new_basename_full_cs):
                            with open(new_basename_full_cs) as f:
                                saved_cs = f.read(1000)  # overflow protection
                            if not isinstance(saved_cs, str):
                                saved_cs = None
                            else:
                                saved_cs = saved_cs.strip().lower()
                    else:
                        raise Exception("programming error")
                else:
                    if os.path.isfile(new_basename_full_cs):
                        os.unlink(new_basename_full_cs)

                if (actual_cs != saved_cs
                        or (actual_cs == saved_cs is None)
                        or actual_cs is None
                        or saved_cs is None
                        or (not os.path.isfile(new_basename_full))
                        ):
                    if os.path.isfile(new_basename_full_cs):
                        os.unlink(new_basename_full_cs)

                    dd_res = downloader.download(
                        i[1],
                        output_path,
                        new_basename=new_basename,
                        stop_event=None,
                        ignore_invalid_connection_security=(
                            options['ignore_invalid_connection_security']
                            ),
                        downloader_obfuscation_required=(
                            options['downloader_obfuscation_required']
                            )
                        )

                    if dd_res == 0:
                        actual_cs = (
                            wayround_org.utils.checksum.make_file_checksum(
                                new_basename_full,
                                options['redownload_prevention_checksum']
                                )
                            )
                        actual_cs = actual_cs.lower()
                        with open(new_basename_full_cs, 'w') as f:
                            f.write(actual_cs)

                for j in wayround_org.utils.tarball.KNOWN_SIGNING_EXTENSIONS:
                    # TODO: this is disabled, as generates too many unneeded
                    #      trafic. need to check in uriexplorer before
                    #      attempting to download
                    continue
                    new_basename_j = new_basename + j
                    jj = wayround_org.utils.path.join(
                        output_path,
                        new_basename_j
                        )

                    if os.path.isfile(jj):
                        if os.stat(jj).st_size == 0:
                            os.unlink(jj)

                    download_uri = '{}{}'.format(i[1], j)
                    self.logger.info(
                        "    download uri: {}".format(download_uri)
                        )

                    if not os.path.isfile(jj):
                        dd_res = downloader.download(
                            download_uri,
                            output_path,
                            new_basename_j,
                            stop_event=None,
                            ignore_invalid_connection_security=(
                                options['ignore_invalid_connection_security']
                                ),
                            downloader_obfuscation_required=(
                                options['downloader_obfuscation_required']
                                )
                            )

                        if dd_res != 0:
                            if os.path.isfile(jj):
                                os.unlink(jj)

            '''
            for i in tarballs_to_delete:
                ij = wayround_org.utils.path.join(output_path, i)
                self.logger.info("removing {}".format(i))
                os.unlink(ij)
            '''

        return
