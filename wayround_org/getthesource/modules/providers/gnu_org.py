
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

import wayround_org.getthesource.modules.providers.templates.std_https_wp


class Provider(
        wayround_org.getthesource.modules.providers.templates.std_https_wp.
        StandardHttpsWithProjects
        ):

    def __init__(self, controller):
        self.cache_dir = controller.cache_dir
        self.logger = controller.logger
        return

    def get_provider_name(self):
        return 'GNU.ORG'

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

    def get_project_param_can_be_None(self):
        return False

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

            if page_parsed is not None:
                tag = page_parsed.find('.//body')

            if tag is not None:
                tag = tag.find('div[@class="inner"]')

            if tag is not None:
                tag = tag.find('div[@id="content"]')

            uls_needed = 2

            if tag is not None:
                ases = list()
                ul_found = False

                for i in tag:

                    if ul_found:
                        if type(i) == lxml.html.HtmlElement:
                            if i.tag == 'a':
                                ir = i.get('href', None)
                                if ir is not None:
                                    ases.append(ir.strip('/'))
                            else:
                                break
                    else:
                        if type(i) == lxml.html.HtmlElement and i.tag == 'ul':
                            uls_needed -= 1
                            if uls_needed == 0:
                                ul_found = True

                ret = ases

                '''
                for i in ['8sync']:
                    while i in ret:
                        ret.remove(i)
                '''

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
                datetime.timedelta(days=1),
                'sha1',
                self.listdir,
                freshdata_callback_args=(project,),
                freshdata_callback_kwargs=dict(path=path, use_cache=False)
                )
            ret = dc.get_data_cache()
        else:

            ret = None, None

            path = '/{}/'.format(path.strip('/'))

            if isinstance(project, str):
                req_url = '{}{}{}'.format(
                    self.get_provider_main_downloads_uri(),
                    project,
                    path
                    )
            else:
                req_url = '{}{}'.format(
                    self.get_provider_main_downloads_uri(),
                    path
                    )

            req_url = '{}/'.format(req_url.rstrip('/'))

            # print("requesting: {}".format(req_url))

            req = urllib.request.Request(req_url)

            page_parsed = None
            try:
                rl_f = urllib.request.urlopen(req)
                resp_code = rl_f.getcode()
                # print("    code: {}".format(resp_code))
                page_text = rl_f.read()
                rl_f.close()
                page_parsed = lxml.html.document_fromstring(page_text)
            except OSError:
                # print("oserror")
                page_parsed = None

            if page_parsed is not None:
                file_list_table = page_parsed.find('.//table')

                if file_list_table is None:
                    pass
                else:

                    file_list_table_tbody = file_list_table

                    folder_trs = file_list_table_tbody.findall('tr')

                    folders = []
                    files = {}

                    for i in folder_trs[2:]:

                        img_alt = None

                        try:
                            img_alt = i[0][0].get('alt', None)
                        except:
                            continue

                        href = None
                        try:
                            href = i[1][0].get('href', None)
                        except:
                            continue

                        if href is not None:
                            href = urllib.request.unquote(href)
                            href = href.strip('/')

                        if img_alt == '[DIR]':
                            folders.append(href)
                        elif img_alt == '[PARENTDIR]':
                            continue
                        elif img_alt == '[   ]':
                            if isinstance(project, str):
                                files[href] = '{}{}'.format(
                                    self.get_provider_main_downloads_uri(),
                                    wayround_org.utils.path.join(
                                        project,
                                        path,
                                        href
                                        )
                                    )
                            else:
                                files[href] = '{}{}'.format(
                                    self.get_provider_main_downloads_uri(),
                                    wayround_org.utils.path.join(
                                        path,
                                        href
                                        )
                                    )

                        else:
                            # NOTE: this is not error. here shoulb be only
                            #       pass
                            pass

                    ret = folders, files
        return ret
