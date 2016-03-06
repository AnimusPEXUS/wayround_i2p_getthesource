
import collections

import wayround_org.webserver.server


def commands():
    ret = collections.OrderedDict([
        ('server', collections.OrderedDict([
            ('run', server_run),
        ]))
    ])
    return ret


def server_run(command_name, opts, args, adds):
    ret = 0
    serv = wayround_org.webserver.server.Server(
        '/etc/wrows.conf'
        #'/home/agu/_local/p/wayround_org_webserver/trunk/test/wrows6.conf'
        )
    serv.start()
    serv.wait_for_shutdown()
    return ret
