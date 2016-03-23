
import datetime
import os.path
import logging

import wayround_org.utils.data_cache
import wayround_org.utils.tarball


class StandardHttps:

    def check_project_param_value(self, value):
        if self.get_project_param_used() is False:
            if value is not None:
                raise ValueError("`project' param nust be None")
        return

    def get_cache_dir(self):
        return self.cache_dir

    def listdir_timeout(self):
        return datetime.timedelta(days=1)

    def tree_timeout(self):
        return datetime.timedelta(days=1)

    def tarballs_timeout(self):
        return datetime.timedelta(days=1)

    def basenames_timeout(self):
        return datetime.timedelta(days=1)

    def walk(self, project, path='/'):

        if self.get_project_param_used() is False:
            if project is not None:
                raise ValueError("`project' param nust be None")

        folders, files = self.listdir(project, path=path)

        if folders is None and files is None:
            #raise Exception("listdir() func returned error")
            self.logger.error(
                "listdir() func returned error: project {}, path {}".format(
                    project,
                    path
                    )
                )
            folders = []
            files = {}

        folders.sort()

        yield path, folders, files

        for i in folders:
            jo = wayround_org.utils.path.join(path, i)
            for j in self.walk(project, jo):
                yield j

        return

    def tree(self, project, use_cache=True):
        """
        result: dict, where keys ar full pathnames relatively
            to project root dir (
            but each line is started with slash!
            )
        """

        self.check_project_param_value(project)

        if use_cache:
            dc = wayround_org.utils.data_cache.ShortCSTimeoutYamlCacheHandler(
                self.cache_dir,
                '({})-(tree)-({})'.format(
                    self.get_provider_name(),
                    project
                    ),
                datetime.timedelta(days=1),
                'sha1',
                self.tree,
                freshdata_callback_args=(project,),
                freshdata_callback_kwargs=dict(use_cache=False)
                )
            ret = dc.get_data_cache()
        else:

            all_files = {}

            for path, dirs, files in self.walk(project):
                for i in files:
                    all_files[wayround_org.utils.path.join(path, i)] = files[i]

            ret = all_files

        return ret

    def tarballs(self, project, use_cache=True, use_tree_cache=True):

        self.check_project_param_value(project)

        if use_cache:
            dc = wayround_org.utils.data_cache.ShortCSTimeoutYamlCacheHandler(
                self.get_cache_dir(),
                '({})-(tarballs)-({})'.format(
                    self.get_provider_name(),
                    project
                    ),
                self.tarballs_timeout(),
                self.get_cs_method_name(),
                self.tarballs,
                freshdata_callback_args=(project, ),
                freshdata_callback_kwargs=dict(use_cache=False)
                )
            ret = dc.get_data_cache()
        else:
            tree = self.tree(project, use_cache=use_tree_cache)

            lst = []

            for i in tree:
                parse_result = wayround_org.utils.tarball.parse_tarball_name(
                    os.path.basename(i),
                    mute=True
                    )
                if parse_result is not None:
                    lst.append((i, tree[i]))

            ret = lst

        return ret

    def basenames(
            self,
            project,
            use_cache=True,
            use_tarballs_cache=True
            ):

        self.check_project_param_value(project)

        if use_cache:
            dc = wayround_org.utils.data_cache.ShortCSTimeoutYamlCacheHandler(
                self.get_cache_dir(),
                '({})-(basenames)-({})'.format(
                    self.get_provider_name(),
                    project

                    ),
                self.basenames_timeout(),
                self.get_cs_method_name(),
                self.basenames,
                freshdata_callback_args=(project,),
                freshdata_callback_kwargs=dict(use_cache=False)
                )
            ret = dc.get_data_cache()
        else:
            tarballs = self.tarballs(project, use_cache=use_tarballs_cache)

            lst = set()

            for i in tarballs:
                parse_result = wayround_org.utils.tarball.parse_tarball_name(
                    os.path.basename(i[0]),
                    mute=True
                    )
                if parse_result is not None:
                    lst.add(parse_result['groups']['name'])

            ret = list(lst)

        return ret
