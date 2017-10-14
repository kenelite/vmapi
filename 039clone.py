#!/usr/bin/env python


import atexit
import argparse
import getpass
import sys
import textwrap
import time

from pyVim import connect
from pyVmomi import vim




# FIX SSL ISSUES WITH PYVMOMI AND PYTHON 2.7.9
import ssl
import requests
context = None

# Disabling urllib3 ssl warnings
requests.packages.urllib3.disable_warnings()

# Disabling SSL certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_NONE

# FIX SSL ISSUES WITH PYVMOMI AND PYTHON 2.7.9


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
    parser.add_argument('-t', '--template',
                        required=True,
                        action='store',
                        help='Template Name of the virtual_machine.')
    parser.add_argument('-n', '--name',
                        required=True,
                        action='store',
                        help='Name of the virtual_machine to look for.')
    parser.add_argument('-c', '--cluster',
                        required=True,
                        action='store',
                        help='ESXi host of the new virtual_machine.')
    parser.add_argument('-cpu', '--cpu',
                        required=False,
                        action='store',
                        help='CPU number of virtual_machine.')
    parser.add_argument('-mem', '--mem',
                        required=False,
                        action='store',
                        help='MEM(G) of virtual_machine.')
    parser.add_argument('-spec', '--customspec',
                        required=False,
                        action='store',
                        help='Name of the customspec.')

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

def get_resource_pool(si, name):
    """
    Find a virtual machine by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.ResourcePool], name)


def get_host_by_name(si, name):
    """
    Find a virtual machine by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.HostSystem], name)

def get_vm_by_name(si, name):
    """
    Find a virtual machine by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.VirtualMachine], name)

def get_cluster(si, name):
    """
    Find a cluster by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.ComputeResource], name)



def main():
    args = get_args()

    # connect to vc
    si = connect.SmartConnect(
        host=args.host,
        user=args.user,
        pwd=args.password,
        port=args.port,
        sslContext=context)
    # disconnect vc
    atexit.register(connect.Disconnect, si)

    content = si.RetrieveContent()

    template_vm = get_vm_by_name(si, args.template)

    customization_spec_name = args.customspec
    guest_customization_spec = si.content.customizationSpecManager.GetCustomizationSpec(name='Linux')

    cluster_name = args.cluster

    cluster = get_cluster(si, cluster_name)

    relocate_spec = vim.vm.RelocateSpec(pool=cluster.resourcePool)

    #relocate_spec = vim.vm.RelocateSpec(pool=resourcePool)

    cloneSpec = vim.vm.CloneSpec(powerOn=False, template=False, location=relocate_spec,
                                 customization=guest_customization_spec.spec)

    task = template_vm.Clone(name=args.name, folder=template_vm.parent, spec=cloneSpec)

    while task.info.state not in [vim.TaskInfo.State.success,
                                  vim.TaskInfo.State.error]:
        time.sleep(5)
        print task.info.state


if __name__ == "__main__":
    main()
