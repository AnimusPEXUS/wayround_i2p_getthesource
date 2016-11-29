#!/usr/bin/python3


def main():

    import sys

    del sys.path[0]

    import logging

    import wayround_i2p.utils.program

    wayround_i2p.utils.program.logging_setup(loglevel='INFO')

    import wayround_i2p.getthesource.commands

    commands = wayround_i2p.getthesource.commands.commands()

    ret = wayround_i2p.utils.program.program('wrogts', commands, None)

    return ret

if __name__ == '__main__':
    exit(main())
