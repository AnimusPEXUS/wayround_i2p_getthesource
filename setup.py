#!/usr/bin/python3

from setuptools import setup

setup(
    name='wayround_org_getthesource',
    version='0.1',
    description='modular tool for downloading lates N (by version numbering) tarballs from given site',
    author='Alexey Gorshkov',
    author_email='animus@wayround.org',
    url='https://github.com/AnimusPEXUS/wayround_org_getthesource',
    install_requires=[
        'wayround_org_utils',
        ],
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)'
        ]
    )
