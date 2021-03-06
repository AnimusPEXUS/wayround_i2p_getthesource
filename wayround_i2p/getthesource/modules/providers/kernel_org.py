
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

import wayround_i2p.utils.path
import wayround_i2p.utils.data_cache
import wayround_i2p.utils.data_cache_miscs
import wayround_i2p.utils.tarball
import wayround_i2p.utils.htmlwalk


import wayround_i2p.getthesource.uriexplorer
import wayround_i2p.getthesource.modules.providers.templates.std_https


class Provider(
        wayround_i2p.getthesource.modules.providers.templates.std_https.
        StandardHttps
        ):

    def __init__(self, controller):

        if not isinstance(
                controller,
                wayround_i2p.getthesource.uriexplorer.URIExplorer
                ):
            raise TypeError(
                "`controller' must be inst of "
                "wayround_i2p.getthesource.uriexplorer.URIExplorer"
                )

        self.cache_dir = controller.cache_dir
        self.logger = controller.logger
        return

    def get_provider_name(self):
        return 'kernel.org'

    def get_provider_code_name(self):
        return 'kernel.org'

    def get_protocol_description(self):
        return 'https'

    def get_is_provider_enabled(self):
        # NOTE: here can be provided warning text printing in case is
        #       module decides to return False. For instance if torsocks
        #       is missing in system and module requires it's presence to be
        #       enabled
        return True

    def get_provider_main_site_uri(self):
        return 'https://www.kernel.org/'

    def get_provider_main_downloads_uri(self):
        return 'https://www.kernel.org/pub/'

    def get_project_param_used(self):
        return False

    def get_cs_method_name(self):
        return 'sha1'

    def get_cache_dir(self):
        return self.cache_dir

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
                '/linux/kernel/people',
                '/linux/devel/gcc',
                '/scm/linux/kernel/git'
                ]:
            return [], {}

        for i in ['.git', '.git_old']:
            if path.endswith(i):
                return [], {}

        if use_cache:
            digest = hashlib.sha1()
            digest.update(path.encode('utf-8'))
            digest = digest.hexdigest().lower()
            dc = wayround_i2p.utils.data_cache.ShortCSTimeoutYamlCacheHandler(
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

            html_walk = wayround_i2p.utils.htmlwalk.HTMLWalk(
                'www.kernel.org'
                )

            path = wayround_i2p.utils.path.join('pub', path)

            folders, files = html_walk.listdir2(path)

            files_d = {}
            for i in files:
                new_uri = '{}{}'.format(
                    'https://www.kernel.org/',
                    wayround_i2p.utils.path.join(
                        path,
                        i
                        )
                    )
                files_d[i] = new_uri

            files = files_d

            ret = folders, files

        return ret
