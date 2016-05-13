
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
        return

    def get_provider_name(self):
        return 'GNU.ORG'

    def get_provider_code_name(self):
        return 'gnu.org'

    def get_protocol_description(self):
        return 'https'

    def get_is_provider_enabled(self):
        # NOTE: here can be provided warning text printing in case is
        #       module decides to return False. For instance if torsocks
        #       is missing in system and module requires it's presence to be
        #       enabled
        return True

    def get_provider_main_site_uri(self):
        return 'https://gnu.org/'

    def get_provider_main_downloads_uri(self):
        return 'https://ftp.gnu.org/gnu/'

    def get_project_param_used(self):
        return True

    def get_cs_method_name(self):
        return 'sha1'

    def get_cache_dir(self):
        return self.cache_dir

    def get_project_names(self, use_cache=True):
        ret = None

        if use_cache:
            dc = wayround_org.utils.data_cache.ShortCSTimeoutYamlCacheHandler(
                self.cache_dir,
                '({})-(project_names)'.format(
                    self.get_provider_name()
                    ),
                datetime.timedelta(days=1),
                'sha1',
                self.get_project_names,
                freshdata_callback_kwargs=dict(use_cache=False)
                )
            ret = dc.get_data_cache()
        else:
            page = None
            try:
                pkg_list_page = urllib.request.urlopen(
                    'https://gnu.org/software/software.html'
                    )
                page_text = pkg_list_page.read()
                pkg_list_page.close()
                page_parsed = lxml.html.document_fromstring(page_text)
            except:
                pass

            tag = None

            # if page_parsed is not None:
            #    tag = page_parsed.find('.//body')

            if page_parsed is not None:
                tag = page_parsed.find(
                    './/div[@class="package-list emph-box"]')

            # if tag is not None:
            #    tag = tag.find('div[@id="content"]')

            print("tag = {}".format(tag))

            uls_needed = 2

            if tag is not None:
                ases = list()

                for i in tag:

                    if type(i) == lxml.html.HtmlElement:
                        if i.tag == 'a':
                            ir = i.get('href', None)
                            if ir is not None:
                                ases.append(ir.strip('/'))
                        else:
                            break

                ret = ases

                for i in ['8sync', 'icecat']:
                    while i in ret:
                        ret.remove(i)

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
                '({})-(listdir)-({})-({})'.format(
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

            ret = None, None

            html_walk = wayround_org.utils.htmlwalk.HTMLWalk('ftp.gnu.org')

            path = wayround_org.utils.path.join('gnu', project, path)

            folders, files = html_walk.listdir2(path)
            if folders is None or files is None:
                folders, files = [], {}

            files_d = {}
            for i in files:
                files_d[i] = '{}{}'.format(
                    self.get_provider_main_downloads_uri(),
                    wayround_org.utils.path.join(
                        # project,
                        path.split('/')[1:],
                        i
                        )
                    )

                #print("files_d[i] : {}".format(files_d[i]))
                #print("project : {}".format(project))
                #print("path : {}".format(path))
                #print("i : {}".format(i))

            files = files_d

            ret = folders, files

        return ret
