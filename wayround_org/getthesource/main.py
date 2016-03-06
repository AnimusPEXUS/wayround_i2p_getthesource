#!/usr/bin/python3

import sys

del sys.path[0]

import logging

import wayround_org.utils.program

wayround_org.utils.program.logging_setup(loglevel='INFO')

import wayround_org.getthesource.commands

commands = wayround_org.getthesource.commands.commands()

ret = wayround_org.utils.program.program('wrogts', commands, None)

exit(ret)
