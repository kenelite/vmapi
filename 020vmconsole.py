#!/usr/bin/env python
# -*- coding: UTF-8 -*-



import atexit
import OpenSSL
import ssl
import sys
import time

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from tools import cli


def get_vm(content, name):
    try:
        name = unicode(name, 'utf-8')
    except TypeError:
        pass

    vm = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True)

    for c in container.view:
        if c.name == name:
            vm = c
            break
    return vm


def get_args():
    """
    Add VM name to args
    """
    parser = cli.build_arg_parser()

    parser.add_argument('-n', '--name',
                        required=True,
                        help='Name of Virtual Machine.')

    args = parser.parse_args()

    return cli.prompt_for_password(args)


def main():
    """
    Simple command-line program to generate a URL
    to open HTML5 Console in Web browser
    """

    args = get_args()

    try:
        si = SmartConnect(host=args.host,
                          user=args.user,
                          pwd=args.password,
                          port=int(args.port))
    except Exception as e:
        print 'Could not connect to vCenter host'
        print repr(e)
        sys.exit(1)

    atexit.register(Disconnect, si)

    content = si.RetrieveContent()

    vm = get_vm(content, args.name)
    vm_moid = vm._moId

    vcenter_data = content.setting
    vcenter_settings = vcenter_data.setting
    console_port = '7331'

    for item in vcenter_settings:
        key = getattr(item, 'key')
        if key == 'VirtualCenter.FQDN':
            vcenter_fqdn = getattr(item, 'value')

    session_manager = content.sessionManager
    session = session_manager.AcquireCloneTicket()

    vc_cert = ssl.get_server_certificate((args.host, int(args.port)))
    vc_pem = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM,
                                             vc_cert)
    vc_fingerprint = vc_pem.digest('sha1')

    print "Open the following URL in your browser to access the " \
          "Remote Console.\n" \
          "You have 60 seconds to open the URL, or the session" \
          "will be terminated.\n"
    print "http://" + args.host + ":" + console_port + "/console/?vmId=" \
          + str(vm_moid) + "&vmName=" + args.name + "&host=" + vcenter_fqdn \
          + "&sessionTicket=" + session + "&thumbprint=" + vc_fingerprint
    print "Waiting for 60 seconds, then exit"
    time.sleep(60)

# Start program
if __name__ == "__main__":
    main()