
import os.path
import sys
import subprocess
import logging
import re
import urllib.request

import lxml.html

OPENJDK_HG_URI = 'http://hg.openjdk.java.net/'

if __name__ == '__main__':

    for i in ['', '.']:
        while i in sys.path:
            sys.path.remove(i)


def tags_path(project_name, package_name, subpackage_name):
    ret = '/{}/{}'.format(project_name, package_name)

    if subpackage_name is not None:
        ret += '/{}'.format(subpackage_name)

    ret += '/tags'

    return ret


def tags_path_jfx(primary_version, subpackage_name):

    if not isinstance(primary_version, int):
        raise TypeError("`primary_version' must be int")

    ret = '/openjfx/{}u-dev'.format(primary_version)

    if subpackage_name is not None:
        ret += '/{}'.format(subpackage_name)

    ret += '/tags'

    return ret


def render_version(
        ver_main,
        ver_update,
        ver_build
        ):
    ret = ''

    ret += '{}'.format(ver_main)

    if ver_update is not None:
        ret += '.{}'.format(ver_update)
    else:
        ret += '.0'

    if ver_build is not None:
        ret += '.{}'.format(ver_build)
    return ret


def gen_tarball_prefix_name(
        subpackage,
        ver_main,
        ver_update,
        ver_build
        ):

    ret = ''

    subpackage_str = ''
    if subpackage is not None:
        subpackage_str = '{}-'.format(subpackage)

    ret += 'jdk-{}'.format(subpackage_str)

    ret += render_version(
        ver_main,
        ver_update,
        ver_build
        )

    return ret

def gen_tarball_prefix_name_jfx(
        ver_main,
        ver_update,
        ver_build
        ):

    ret = 'openjfx-'

    ret += render_version(
        ver_main,
        ver_update,
        ver_build
        )

    return ret


def download_tarball(
        tarball_page_uri,
        output_filename,
        preferred_extension='bz2'
        ):

    page_text = None
    with urllib.request.urlopen(tarball_page_uri) as f:
        page_text = f.read()

    page_text = lxml.html.document_fromstring(page_text)

    all_hrefs = page_text.findall('.//a')

    tarball_uri = None

    for i in all_hrefs:
        if i.text == preferred_extension:
            tarball_uri = i.get('href', None)
            break

    del all_hrefs

    if isinstance(tarball_uri, str):
        tarball_uri = OPENJDK_HG_URI + tarball_uri

        os.makedirs(os.path.dirname(output_filename), exist_ok=True)

        p = subprocess.Popen(
            [
                'wget',
                '-c',
                '-O',
                output_filename,
                tarball_uri
                ]
            )

        p.wait()

    return


def get_tag_rev_uri(project_name, package_name, subpackage_name, tag):

    ret = None

    t_path = tags_path(project_name, package_name, subpackage_name)
    print("t_path: {}".format(t_path))
    tags_page_uri = OPENJDK_HG_URI + t_path.lstrip('/')

    page_text = None
    print("tags_page_uri: {}".format(tags_page_uri))
    with urllib.request.urlopen(tags_page_uri) as f:
        page_text = f.read()

    page_text = lxml.html.document_fromstring(page_text)

    all_hrefs = page_text.findall('.//a')

    print("found hrefs: {}".format(len(all_hrefs)))

    for i in all_hrefs:
        # print("i.text: {}\n\n".format(i.text))
        if i.text is not None and i.text.strip() == tag:
            ret = i.get('href', None)
            break

    if isinstance(ret, str):
        ret = OPENJDK_HG_URI + ret.lstrip('/')

    return ret


def get_tag_rev_uri_jfx(primary_version, subpackage_name, tag):

    ret = None

    t_path = tags_path_jfx(primary_version, subpackage_name)
    
    print("t_path: {}".format(t_path))
    
    tags_page_uri = OPENJDK_HG_URI + t_path.lstrip('/')

    page_text = None
    print("tags_page_uri: {}".format(tags_page_uri))
    with urllib.request.urlopen(tags_page_uri) as f:
        page_text = f.read()

    page_text = lxml.html.document_fromstring(page_text)

    all_hrefs = page_text.findall('.//a')

    print("found hrefs: {}".format(len(all_hrefs)))

    for i in all_hrefs:
        # print("i.text: {}\n\n".format(i.text))
        if i.text is not None and i.text.strip() == tag:
            ret = i.get('href', None)
            break

    if isinstance(ret, str):
        ret = OPENJDK_HG_URI + ret.lstrip('/')

    return ret


def jdk_routine(requested_tag):
    ret = 0

    re_res = re.match(
        r'jdk(?P<main>\d+)(u(?P<update>\d+))?(\-b(?P<build>\d+))?',
        requested_tag
        )

    if re_res is None:
        ret = 2

    if ret == 0:

        ver_main = re_res.group('main')
        ver_update = re_res.group('update')
        ver_build = re_res.group('build')

        project_name = 'jdk{}'.format(ver_main)
        if ver_update is not None:
            project_name += 'u'

    if ret == 0:

        sub_proj_list = [
            None, 'corba', 'hotspot', 'jaxp',
            'jaxws', 'jdk', 'langtools',
            'nashorn'
            ]

        package_name = project_name

        for i in sub_proj_list:
            get_tag_rev_uri_args = (
                project_name,
                package_name,
                i,
                requested_tag
                )
            print("get_tag_rev_uri args: {}".format(get_tag_rev_uri_args))
            tag_rev_uri = get_tag_rev_uri(*get_tag_rev_uri_args)
            print("  tag_rev_uri: {}".format(tag_rev_uri))
            tarball_prefix_name = gen_tarball_prefix_name(
                i,
                ver_main,
                ver_update,
                ver_build
                )
            print('tarball_prefix_name: {}'.format(tarball_prefix_name))
            ver_str = render_version(
                ver_main,
                ver_update,
                ver_build
                )
            print('ver_str: {}'.format(ver_str))
            download_tarball(
                tag_rev_uri,
                os.path.join(
                    PPWD,
                    'downloads',
                    project_name,
                    'jdk-{}'.format(ver_str),
                    tarball_prefix_name + '.tar.bz2'
                    ),
                'bz2'
                )
            print()
    return ret


def jfx_routine(requested_tag, working_dir):
    ret = 0

    re_res = re.match(
        r'(?P<main>\d+)(u(?P<update>\d+))?(\-b(?P<build>\d+))?',
        requested_tag
        )

    if re_res is None:
        ret = 2

    if ret == 0:

        ver_main = re_res.group('main')
        ver_update = re_res.group('update')
        ver_build = re_res.group('build')

        project_name = 'openjfx{}'.format(ver_main)
        if ver_update is not None:
            project_name += 'u'

    if ret == 0:

        get_tag_rev_uri_args = (
            int(ver_main), 
            'rt', 
            requested_tag
            )
        print("get_tag_rev_uri args: {}".format(get_tag_rev_uri_args))
        tag_rev_uri = get_tag_rev_uri_jfx(*get_tag_rev_uri_args)
        print("  tag_rev_uri: {}".format(tag_rev_uri))
        tarball_prefix_name = gen_tarball_prefix_name_jfx(
            ver_main,
            ver_update,
            ver_build
            )
        print('tarball_prefix_name: {}'.format(tarball_prefix_name))
        ver_str = render_version(
            ver_main,
            ver_update,
            ver_build
            )
        print('ver_str: {}'.format(ver_str))
        download_tarball(
            tag_rev_uri,
            os.path.join(
                working_dir,
                'downloads',
                project_name,
                'openjfx-{}'.format(ver_str),
                tarball_prefix_name + '.tar.bz2'
                ),
            'bz2'
            )
        print()
    return ret
