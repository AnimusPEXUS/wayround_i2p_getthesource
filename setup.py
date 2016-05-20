#!/usr/bin/python3

from setuptools import setup

setup(
    name='wayround_org_getthesource',
    version='0.2.8',
    description=(
        "modular tool for downloading lates N"
        " (by version numbering) tarballs from given site"
        ),
    author='Alexey Gorshkov',
    author_email='animus@wayround.org',
    url='https://github.com/AnimusPEXUS/wayround_org_getthesource',
    install_requires=[
        'wayround_org_utils',
        'regex',
        'pyyaml'
        ],
    classifiers=[
        'License :: OSI Approved'
        ' :: GNU General Public License v3 or later (GPLv3+)'
        ],
    packages=[
        'wayround_org.getthesource',
        'wayround_org.getthesource.modules',
        'wayround_org.getthesource.modules.downloaders',
        'wayround_org.getthesource.modules.providers',
        'wayround_org.getthesource.modules.providers.templates'
        ],
    entry_points={
        'console_scripts': [
            'wrogts = wayround_org.getthesource.main'
            ]
        }
    )
