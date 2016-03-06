
"""
Module for getting tarballs and they' related information from gnu.org
"""

import os.path
import logging
import urllib.request
import datetime

import yaml
import lxml.html

import wayround_org.utils.path
import wayround_org.utils.data_cache


class Provider:

    def __init__(self, controller):
        self.cache_dir = controller.cache_dir
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
        return True

    def _get_project_names_cache_check_refresh_required_cb(self, path):

        ret = True

        if os.path.isfile(path):

            file_ctime = datetime.datetime.fromtimestamp(
                os.stat(path).st_ctime,
                tz=datetime.timezone.utc
                )
            current_time = datetime.datetime.now(
                tz=datetime.timezone.utc
                )

            ret = (current_time - file_ctime) > datetime.timedelta(days=1)

        return ret

    def _get_project_names_cache_refresh_cb(self, path):
        data = self.get_project_names(use_cache=False)
        with open(path, 'w') as f:
            f.write(yaml.dump(data))
        return

    def _get_project_names_cache(self):
        cache_mgr = wayround_org.utils.data_cache.DataCache(
            self.cache_dir,
            '{}_project_names'.format(
                self.get_provider_name()
                ),
            self._get_project_names_cache_check_refresh_required_cb,
            tuple(),
            {},
            self._get_project_names_cache_refresh_cb,
            tuple(),
            {}
            )
        ret = None
        cache = cache_mgr.open_cache()
        if cache is not None:
            ret = yaml.load(cache.read())
            cache.close()
        return ret

    def get_project_names(self, use_cache=True):
        ret = None

        if use_cache:
            ret = self._get_project_names_cache()
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

        return ret

    def get_basenames(self, project):
        return

    def listdir(self, project, path='/'):
        """
        params:
            project - str or None. None - allows listing directory /gnu/

        result:
            dirs - string list of directory base names
            files - dict in which keys are file base names and values are
                complete urls for download

            dirs == files == None - means error
        """

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

        print('req_url: {}'.format(req_url))

        req = urllib.request.Request(req_url)

        page_parsed = None
        try:
            rl_f = urllib.request.urlopen(req)
            page_text = rl_f.read()
            rl_f.close()
            page_parsed = lxml.html.document_fromstring(page_text)
        except OSError:
            page_parsed = None

        if page_parsed is not None:
            file_list_table = page_parsed.find('.//table')

            if file_list_table is None:
                pass
            else:

                # file_list_table_tbody = file_list_table.find('tbody')

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
                        pass

                ret = folders, files

        return ret

    def walk(self, project, path='/'):

        folders, files = self.listdir(project, path=path)

        if folders is None and files is None:
            raise Exception("listdir() func returned error")

        yield path, folders, files

        for i in folders:
            jo = wayround_org.utils.path.join(path, i)
            for j in self.walk(project, jo):
                yield j

        return

    def tree(self, project):
        """
        result: dict, where keys ar full pathnames relatively to project root dir (
            but each line is started with slash!
            )
        """

        all_files = {}

        for path, dirs, files in self.walk(project):
            for i in files:
                all_files[wayround_org.utils.path.join(path, i)] = files[i]

        return all_files
