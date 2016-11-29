#!/usr/bin/python3

from setuptools import setup

setup(
    name='wayround_i2p_getthesource',
    version='0.2.10',
    description=(
        "modular tool for downloading lates N"
        " (by version numbering) tarballs from given site"
        ),
    author='Alexey Gorshkov',
    author_email='animus@wayround.org',
    url='https://github.com/AnimusPEXUS/wayround_i2p_getthesource',
    install_requires=[
        'wayround_i2p_utils',
        'regex',
        'pyyaml'
        ],
    classifiers=[
        'License :: OSI Approved'
        ' :: GNU General Public License v3 or later (GPLv3+)'
        ],
    packages=[
        'wayround_i2p.getthesource',
        'wayround_i2p.getthesource.modules',
        'wayround_i2p.getthesource.modules.downloaders',
        'wayround_i2p.getthesource.modules.providers',
        'wayround_i2p.getthesource.modules.providers.templates'
        ],
    entry_points={
        'console_scripts': [
            'wrogts = wayround_i2p.getthesource.main:main'
            ]
        }
    )
