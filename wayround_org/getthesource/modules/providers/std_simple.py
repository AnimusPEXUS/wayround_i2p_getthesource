
import os.path
import fnmatch
import hashlib
import regex
import ftplib

import wayround_org.utils.path
import wayround_org.utils.htmlwalk
import wayround_org.utils.ftpwalk

import wayround_org.getthesource.modules.providers.templates.std_https


class Provider(
        wayround_org.getthesource.modules.providers.templates.std_https.
        StandardHttps
        ):

    def __init__(self, controller):
        if not isinstance(
                controller,
                wayround_org.getthesource.uriexplorer.URIExplorer
                ):
            raise TypeError(
                "`controller' must be inst of "
                "wayround_org.getthesource.uriexplorer.URIExplorer"
                )

        self.cache_dir = controller.cache_dir
        self.logger = controller.logger

        self._inmemory_cache_for_tarballs = None

        self.simple_config = controller.simple_config
        self.ftp_client = None
        return

    def get_provider_name(self):
        return 'std_simple'

    def get_provider_code_name(self):
        return 'std_simple'

    def get_protocol_description(self):
        return ['https', 'http', 'ftp']

    def get_is_provider_enabled(self):
        return False

    def get_provider_main_site_uri(self):
        return None

    def get_provider_main_downloads_uri(self):
        return None

    def get_project_param_used(self):
        return False

    def get_cs_method_name(self):
        return 'sha1'

    def listdir(self, project, path='/', use_cache=True):
        """
        params:
            project - str or None. None - allows listing directory /gnu/

        result:
            dirs - string list of directory base names
            files - dict in which keys are file base names and values are
                complete urls for download

            dirs == files == None - means error
        """

        if project is not None:
            raise ValueError(
                "`project' for `std_simple' provider must always be None"
                )

        #'''
        exclude_paths = self.simple_config.get('exclude_paths', [])
        exclude_paths_re = self.simple_config.get('exclude_paths_re', [])
        exclude_paths_bases = self.simple_config.get('exclude_paths_bases', [])
        exclude_paths_bases_re = (
            self.simple_config.get('exclude_paths_bases_re', [])
            )
        reject_files = self.simple_config.get('reject_files', [])
        reject_files_re = self.simple_config.get('reject_files_re', [])
        #'''

        target_uri = self.simple_config.get('target_uri', None)

        uri_obj = wayround_org.utils.uri.HttpURI.new_from_string(target_uri)
        uri_obj_copy = uri_obj.copy()
        uri_obj_copy.path = None
        target_uri_with_root_path = str(uri_obj_copy)
        target_uri_path = uri_obj.path

        del uri_obj_copy

        if uri_obj.scheme not in ['http', 'https', 'ftp']:
            raise ValueError(
                "Invalid URI scheme: not supported: {}".format(uri_obj.scheme)
                )

        #'''
        for i in exclude_paths:
            if fnmatch.fnmatch(path, i):
                return [], {}

        for i in exclude_paths_bases:
            if fnmatch.fnmatch(os.path.basename(path), i):
                return [], {}

        for i in exclude_paths_re:
            if regex.match(i, path):
                return [], {}

        for i in exclude_paths_bases_re:
            if regex.match(i, os.path.basename(path)):
                return [], {}
        #'''

        if use_cache:
            digest = hashlib.sha1()
            digest.update(
                wayround_org.utils.path.join(
                    uri_obj.path,
                    path
                    ).encode('utf-8')
                )
            digest = digest.hexdigest().lower()
            dc = wayround_org.utils.data_cache.ShortCSTimeoutYamlCacheHandler(
                self.cache_dir,
                '({})-(for {})-(listdir)-({})'.format(
                    self.get_provider_name(),
                    uri_obj.authority.host,
                    digest
                    ),
                self.listdir_timeout(),
                'sha1',
                self.listdir,
                freshdata_callback_args=(project, ),
                freshdata_callback_kwargs=dict(path=path, use_cache=False)
                )
            ret = dc.get_data_cache()
        else:
            self.logger.info("getting listdir at: {}".format(path))

            ret = None, None

            walker_obj = None
            walker_obj_listdir_method = None

            if uri_obj.scheme in ['http', 'https']:

                walker_obj = wayround_org.utils.htmlwalk.HTMLWalk(
                    uri_obj.authority.host,
                    scheme=uri_obj.scheme,
                    port=uri_obj.authority.port
                    )
                walker_obj_listdir_method = walker_obj.listdir2

            elif uri_obj.scheme in ['ftp']:
                if self.ftp_client is None:
                    self.ftp_prefix_uri = 'ftp://{}'.format(
                        uri_obj.authority.host
                        )
                    self.ftp_client = ftplib.FTP(
                        uri_obj.authority.host,
                        user='anonymous'
                        )
                    self.ftp_walk = wayround_org.utils.ftpwalk.FTPWalk(
                        self.ftp_client
                        )
                walker_obj = self.ftp_client
                walker_obj_listdir_method = self.ftp_listdir

            else:
                raise Exception("programming error")

            path = wayround_org.utils.path.join('/', uri_obj.path, path)

            #print("getting list for: {}".format(path))
            folders, files = walker_obj_listdir_method(path)
            #print("    result: {}".format((folders, files)))

            if folders is not None and files is not None:

                files_d = {}
                for i in files:
                    new_uri = '{}{}'.format(
                        target_uri_with_root_path,
                        wayround_org.utils.path.join(path, i).lstrip('/')
                        )
                    files_d[i] = new_uri

                files = files_d

                ret = folders, files

        #'''
        if ret[0] is not None:

            files = ret[1]

            for i in list(files.keys()):
                for j in reject_files:
                    if fnmatch.fnmatch(i, j):
                        if i in files:
                            del files[i]

            for i in list(files.keys()):
                for j in reject_files_re:
                    if regex.match(j, i):
                        if i in files:
                            del files[i]

            ret = ret[0], files
        #'''

        return ret

    def ftp_listdir(self, path):
        ret = None, None

        lst = self.ftp_walk.listdir(path)

        if isinstance(lst, list):

            dirs = []
            files = {}

            for i in lst:

                if i in ['..', '.', '/']:
                    continue

                ij = wayround_org.utils.path.join(path, i)

                if not self.ftp_walk.is_dir(ij):
                    files[i] = '{}{}'.format(self.ftp_prefix_uri, ij)
                else:
                    dirs.append(i)

            ret = dirs, files
        return ret

    # FIXME: such mesures shuld not be used
    #       (fixed with a46ec590daf999573f9f6e9f598028235d3bb883)
    def tarballs(self, project, use_cache=True, use_tree_cache=True):
        if self._inmemory_cache_for_tarballs is None:
            self._inmemory_cache_for_tarballs = super().tarballs(
                project,
                use_cache=use_cache,
                use_tree_cache=use_tree_cache
                )
        return self._inmemory_cache_for_tarballs
