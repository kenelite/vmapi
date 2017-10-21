#!/usr/bin/env python


import atexit
import argparse
import getpass
import sys
import textwrap
import time

from pyVim import connect
from pyVmomi import vim





import requests
requests.packages.urllib3.disable_warnings()

import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

def get_args():
    parser = argparse.ArgumentParser()

    # because -h is reserved for 'help' we use -s for service
    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vSphere service to connect to')

    # because we want -p for password, we use -o for port
    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use when connecting to host')
    parser.add_argument('-e', '--esxi',
                        required=True,
                        action='store',
                        help='Name of the ESXi to look for.')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
                   (args.host, args.user))

    return args



def _get_obj(content, vimtype, name):
    """
    Get the vsphere object associated with a given text name
    """
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj




def get_host_by_name(si, name):
    """
    Find a virtual machine by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.HostSystem], name)


# form a connection...
args = get_args()
si = connect.SmartConnect(host=args.host, user=args.user, pwd=args.password,
                          port=args.port)

# doing this means you don't need to remember to disconnect your script/objects
atexit.register(connect.Disconnect, si)

# search the whole inventory tree recursively... a brutish but effective tactic
content = si.RetrieveContent()

esxihost = get_host_by_name(si, args.esxi)

if esxihost:
    print('ESXi Name               : {}'.format(esxihost.name))
    print('ESXi CPU Detail         : Processor Sockets: {}, Cores per Socket {}'.format(
        esxihost.summary.hardware.numCpuPkgs,
        (esxihost.summary.hardware.numCpuCores / esxihost.summary.hardware.numCpuPkgs)))
    print('ESXi CPU Type           : {}'.format(esxihost.summary.hardware.cpuModel))
    print('ESXi CPU Usage          : Used: {} Mhz, Total: {} Mhz'.format(
        esxihost.summary.quickStats.overallCpuUsage,
        (esxihost.summary.hardware.cpuMhz * esxihost.summary.hardware.numCpuCores)))
    print('ESXi Memory Usage       : Used: {:.0f} GB, Total: {:.0f} GB\n'.format(
        (float(esxihost.summary.quickStats.overallMemoryUsage) / 1024),
        (float(esxihost.summary.hardware.memorySize) / 1024 / 1024 / 1024)))

    for each_ds in esxihost.datastore:
        print('Datastore Name          : {}'.format(each_ds.name))
        print('Datastore Capacity      : {:.1f}GB '.format(float(each_ds.summary.capacity) /1024/1024/1024))
        print('Datastore FreeSpace     : {:.1f}GB'.format(float(each_ds.summary.freeSpace) /1024/1024/1024))

else:
    print('ESXi {} not found'.format(args.esxi))


sys.exit(0)