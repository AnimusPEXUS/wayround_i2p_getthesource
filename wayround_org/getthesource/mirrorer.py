
import os.path
import importlib

import yaml

import wayround_org.utils.path
import wayround_org.utils.tarball
import wayround_org.utils.version
import wayround_org.utils.checksum
import wayround_org.utils.uri
import wayround_org.utils.list

import wayround_org.getthesource.uriexplorer


def get_default_mirroring_cfg():
    ret = {
        'preferred_tarball_compressors': (
            wayround_org.utils.tarball.
            ACCEPTABLE_SOURCE_NAME_EXTENSIONS
            ),
        'only_latests': 3,
        'ignore_invalid_connection_security': False,

        # NOTE: using and enabling this may be unsafe
        'delete_old_tarballs': False,

        'downloader_obfuscation_required': False,
        'redownload_prevention_checksum': 'sha512',
        # 'separate_dirs_by_bases': True
        }
    return ret


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
            wayround_org.utils.path.join(self.working_path, 'wrogts-logs'),
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

        self.pers_prov_obj = None

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

        if self.simple_config is not None:
            provider_name = 'std_simple'
            project_names = None
            mirroring_options = get_default_mirroring_cfg()
            if self.perform_mirroring(
                    path,
                    provider_name,
                    project_names,
                    mirroring_options
                    ) != 0:
                ret = 2
        else:

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
                for i in m_cfg:
                    if not isinstance(i, dict):
                        self.logger.error(
                            "config error: all 0 level entries must be dicts"
                            )
                        ret = 1
                        break

            if ret == 0:

                for i in m_cfg:

                    provider_name = i.get('provider_name', None)
                    if provider_name is None:
                        self.logger.error("provider name should be supplied")
                        ret = 3
                        continue

                    project_names = i.get('project_names', None)

                    mirroring_options = get_default_mirroring_cfg()

                    _t = i.get('mirroring_opt', None)
                    if isinstance(_t, dict):
                        mirroring_options.update(_t)

                    if self.perform_mirroring(
                            path,
                            provider_name,
                            project_names,
                            mirroring_options
                            ) != 0:
                        ret = 2
        return ret

    def perform_mirroring(
            self,
            path,
            provider_name,
            project_names,
            mirroring_options
            ):

        ret = 0

        path = wayround_org.utils.path.abspath(path)

        self.logger.info("loading provider: {}".format(provider_name))

        provider_obj = self.uriexplorer.get_provider(provider_name)

        if isinstance(project_names, str):
            project_names = [project_names]

        if project_names is None and provider_obj.get_project_param_used():
            project_names = provider_obj.get_project_names()

            if project_names is None:
                self.logger.error(
                    "can't get project list for provider `{}'".format(
                        provider_name
                        )
                    )
                ret = 2

        if ret == 0:

            if project_names is None:
                project_names = [None]

        if ret == 0:

            self.logger.info(
                "processing {} project names".format(len(project_names))
                )

            for project_name in sorted(project_names):

                basenames = provider_obj.basenames(project_name)

                for basename in sorted(basenames):
                    if self.work_on_dir_with_basename(
                            path,
                            provider_name,
                            project_name,
                            basename,
                            mirroring_options
                            ) != 0:
                        ret = 3

        return ret

    def work_on_dir_with_basename(
            self,
            path,
            provider,
            project,
            basename,
            options
            ):

        ret = 0

        self.logger.info(
            "task: {}, {}, {}".format(provider, project, basename)
            )

        path = wayround_org.utils.path.abspath(path)

        if provider == 'std_simple' and self.pers_prov_obj is not None:
            provider_obj = self.pers_prov_obj
        else:
            provider_obj = self.uriexplorer.get_provider(provider)
            self.pers_prov_obj = provider_obj

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
        tarballs = provider_obj.tarballs(project)  # [provider][]
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

        needed_tarballs = self.apply_filters(
            needed_tarballs,
            options.get('filter_lines', [])
            )

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
                "  {} file(s) are marked for download: {}".format(
                    len(tarballs_to_download),
                    [os.path.basename(i[0]) for i in tarballs_to_download]
                    )
                )

            self.logger.info(
                "  {} file(s) are marked for deletion: {}".format(
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

        return ret

    def apply_filters(
            self,
            needed_tarballs,
            filter_text_or_lines
            ):

        if not isinstance(filter_text_or_lines, (list, str)):
            raise TypeError(
                "`filter_text_or_lines' must be str or list of str"
                )

        if isinstance(filter_text_or_lines, list):
            filter_text_or_lines = '\n'.join(filter_text_or_lines)

        lst = set(
            wayround_org.utils.list.filter_list(
                [x[0] for x in needed_tarballs],
                filter_text_or_lines
                )
            )

        ret = []

        for i in needed_tarballs:
            if i[0] in lst:
                ret.append(i)

        return ret
