
"""
Module for getting tarballs and they' related information from gnu.org
"""

import os.path
import logging
import urllib.request
import datetime
import hashlib

import yaml
import lxml.html

import wayround_org.utils.path
import wayround_org.utils.data_cache
import wayround_org.utils.data_cache_miscs
import wayround_org.utils.tarball
import wayround_org.utils.htmlwalk


import wayround_org.getthesource.uriexplorer
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
        return

    def get_provider_name(self):
        return 'GNOME.ORG'

    def get_provider_code_name(self):
        return 'gnome.org'

    def get_protocol_description(self):
        return 'https'

    def get_is_provider_enabled(self):
        return True

    def get_provider_main_site_uri(self):
        return 'https://www.gnome.org/'

    def get_provider_main_downloads_uri(self):
        return 'https://download.gnome.org/sources/'

    def get_project_param_used(self):
        return False

    def get_cs_method_name(self):
        return 'sha1'

    def get_cache_dir(self):
        return self.cache_dir

    def listdir_timeout(self):
        return datetime.timedelta(days=10)

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
                "`project' for `kernel.org' provider must always be None"
                )

        if path in [
                ]:
            return [], {}

        if path.endswith('.git'):
            return [], {}

        if use_cache:
            digest = hashlib.sha1()
            digest.update(path.encode('utf-8'))
            digest = digest.hexdigest().lower()
            dc = wayround_org.utils.data_cache.ShortCSTimeoutYamlCacheHandler(
                self.cache_dir,
                '({})-(listdir)-({})'.format(
                    self.get_provider_name(),
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

            html_walk = wayround_org.utils.htmlwalk.HTMLWalk(
                'download.gnome.org'
                )

            path = wayround_org.utils.path.join('sources', path)

            folders, files = html_walk.listdir2(path)

            files_d = {}
            for i in files:
                new_uri = '{}{}'.format(
                    'https://download.gnome.org/',
                    wayround_org.utils.path.join(
                        path,
                        i
                        )
                    )
                files_d[i] = new_uri

            files = files_d

            ret = folders, files

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
