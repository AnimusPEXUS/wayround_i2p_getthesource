
import yaml
import copy

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

        return

    def work_on_dir(self, path):

        ret = 0

        path = wayround_org.utils.path.abspath(path)

        m_cfg_path = wayround_org.utils.path.join(
            path,
            'wrogts_mirrorer.conf.yaml'
            )

        with open(m_cfg_path) as f:
            m_cfg = yaml.load(f.read())

        if not isinstance(m_cfg, list):
            self.logger.error(
                "invalid structure of {}".format(m_cfg_path)
                )
            ret = 1

        if ret == 0:
            for i in m_cfg:
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

                targets = []

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
            # else, if list, assume list of tarball basenames to get
            'gnu.org': {
                'gcc': [  # list of tarball basenames to get
                    'gcc'
                ]
            }
        }
        """

        ret = 0

        errors_oqcured = False

        requested_provider_names = list(settings.keys())

        requested_provider_names.sort()

        for provider_name in requested_provider_names:
            if provider_name not in self.uriexplorer.list_providers():
                self.logger.error(
                    "No requested provider named: {}".format(provider_name)
                    )
                errors_occured = True
                continue
            provider_target_setting = settings[provider_name]
            if isinstance(provider_target_setting, list):
                pass
            elif isinstance(provider_target_setting, dict):
                for i in provider_target_setting.keys():
                    pass
            else:
                self.logger.error(
                    "invalid type of target descr structure for provider:"
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
            
            self.remove_invalid_bases(bases)

            self.filter_for_latests(
                filter_for_latests_res,
                0,
                bases
                )

            '''
            needed_versions = []

            versions = set()

            for i in needed_tarballs:
                parse_result = wayround_org.utils.tarball.parse_tarball_name(
                    i[0]
                    )
                if parse_result is None:
                    continue

                if parse_result[]
            '''
        return
    
    def remove_invalid_bases(self, bases):
        for i in range(len(bases) - 1, -1, -1):
            parse_result = wayround_org.utils.tarball.parse_tarball_name(
                bases[i][0]
                )
            if parse_result is None:
                del bases[i]
            else:
                try:
                    version_list = parse_result['groups']['version_list']
                except KeyError:
                    version_list = None

                if (not isinstance(version_list, list)
                        or len(version_list) == 0):
                    del bases[i]
        return

    def filter_for_latests(
            self,
            filter_for_latests_res,
            version_depth_index,
            farther_variants,
            trim_count
            ):
        """
        This method is for recursive calling
        """
        # TODO: maybe this method need to be moved into utils

        # farther_variants.sort()
        farther_variants_working = copy.copy(farther_variants)

        version_index_list = set()

        for i in farther_variants_working:
            parse_result = wayround_org.utils.tarball.parse_tarball_name(
                i[0]
                )

            version_list = parse_result['groups']['version_list']

            if version_depth_index >= len(version_list):
                version_index_list.add(0)
            else:
                version_index_list.add(int(version_list[version_depth_index]))

        version_index_list = list(version_index_list)
        version_index_list.sort(reverse=True)

        # version_index_list = version_index_list[:trim_count]

        farther_variants_dicts = dict()

        for i in version_index_list:
            
            if not i in farther_variants_dicts:
                farther_variants_dicts[i] = []

            for j in farther_variants_working:
                parse_result = wayround_org.utils.tarball.parse_tarball_name(
                    j[0]
                    )

                version_list = parse_result['groups']['version_list']

                if version_depth_index >= len(version_list):
                    version_index_value = 0
                else:
                    version_index_valueint(version_list[version_depth_index])

                if version_index_value in version_index_list:
                    farther_variants_dicts[]
                    del farther_variants_working[i]

        return
