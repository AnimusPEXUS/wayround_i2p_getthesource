
"""
Module for getting tarballs and they' related information from gnu.org
"""

import os.path
import logging
import urllib.request
import datetime
import hashlib
import fnmatch

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
        return

    def get_provider_name(self):
        return 'LAUNCHPAD.NET'

    def get_provider_code_name(self):
        return 'launchpad.net'

    def get_protocol_description(self):
        return 'https'

    def get_is_provider_enabled(self):
        # NOTE: here can be provided warning text printing in case is
        #       module decides to return False. For instance if torsocks
        #       is missing in system and module requires it's presence to be
        #       enabled
        return True

    def get_provider_main_site_uri(self):
        return 'https://launchpad.net/'

    def get_provider_main_downloads_uri(self):
        return 'https://launchpad.net/'

    def get_project_param_used(self):
        return True

    def get_cs_method_name(self):
        return 'sha1'

    def get_cache_dir(self):
        return self.cache_dir

    def get_project_names(self, use_cache=True):

        ret = None

        return ret

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

        if use_cache:
            digest = hashlib.sha1()
            digest.update(path.encode('utf-8'))
            digest = digest.hexdigest().lower()
            dc = wayround_org.utils.data_cache.ShortCSTimeoutYamlCacheHandler(
                self.cache_dir,
                '({})-(launchpad.net)-(listdir)-({})-({})'.format(
                    self.get_provider_name(),
                    project,
                    digest
                    ),
                self.listdir_timeout(),
                'sha1',
                self.listdir,
                freshdata_callback_args=(project,),
                freshdata_callback_kwargs=dict(path=path, use_cache=False)
                )
            ret = dc.get_data_cache()
        else:

            self.logger.info("searching in: {}".format(path))

            ret = None, None

            with urllib.request.urlopen(
                    'https://launchpad.net/{project}/+download'.format(
                        project=project
                        )
                    ) as f:
                download_page_txt = f.read()

            doc = lxml.html.document_fromstring(download_page_txt)

            folders = []
            files = {}
            hrefs = set()

            while True:

                for i in doc.findall('.//a'):
                    hrefs.add(urllib.request.unquote(i.get('href', '')))

                next_a = doc.find('.//a[@class="next"]')

                if next_a is None:
                    break

                next_a = next_a.get('href', None)

                if next_a is None:
                    break

                self.logger.info("getting additioanl page: {}".format(next_a))

                with urllib.request.urlopen(next_a) as f:
                    download_page_txt = f.read()

                doc = lxml.html.document_fromstring(download_page_txt)

            hrefs -= set([''])

            for i in hrefs:
                if fnmatch.fnmatch(
                        i,
                        'https://launchpad.net/{project}/*.tar*'.format(
                            project=project
                            )
                        ):

                    files[os.path.basename(i)] = i

            ret = folders, files

        return ret
