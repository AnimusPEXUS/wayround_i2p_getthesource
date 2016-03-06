
import wayround_org.getthesource.data_cache


class Controller:

    def __init__(self, cfg):
        self.cfg = cfg

    def load_providers(self):
        return

    def get_providers(self):
        return

    def get_tarball_uris(self, basename, provider, project):
        """
        this method returns list with 2-tuples, where
            tuple[0] - is tarball base filename
            tuple[1] - complete url to get it

        basename - string - base name of tarballs to search for.
            for instance: 'wine', 'gcc', 'gcc-core', 'linux' etc.

        provider parameter can be None, string or list of strings, where
            None - means to try all providers GetTheSource knows of
            list - same as None, but try only listed providers
            string - treated as list of strings with single item

        project parameter can be None, string or list of strings:
            some providers can be additioanlly subdivided by projects, and
            can not be treeted as one pice. this is sf.net for instance,
            where only few projects of all resembles some usefull items. so in
            case of sf.net, project with value of None - means - get
            all usefull project names of sf.net and search for tarballs with
            basename among them, but is project name is string or list for
            strings, search only among listed projects

            None - search among all projects, all useful projects or among
                entire provider site, depending on nature of provider in
                question
            list - same as None, but try only listed projects
            string - treated as list of strings with single item
        """

        return
