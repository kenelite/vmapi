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
    parser.add_argument('-n', '--name',
                        required=True,
                        action='store',
                        help='Name of the virtual_machine to look for.')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
                   (args.host, args.user))

    return args


def _create_char_spinner():
    """Creates a generator yielding a char based spinner.
    """
    while True:
        for c in '|/-\\':
            yield c


_spinner = _create_char_spinner()


def spinner(label=''):
    """Prints label with a spinner.

    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    sys.stdout.write("\r\t%s %s" % (label, _spinner.next()))
    sys.stdout.flush()


def answer_vm_question(virtual_machine):
    print "\n"
    choices = virtual_machine.runtime.question.choice.choiceInfo
    default_option = None
    if virtual_machine.runtime.question.choice.defaultIndex is not None:
        ii = virtual_machine.runtime.question.choice.defaultIndex
        default_option = choices[ii]
    choice = None
    while choice not in [o.key for o in choices]:
        print "VM power on is paused by this question:\n\n"
        print "\n".join(textwrap.wrap(
            virtual_machine.runtime.question.text, 60))
        for option in choices:
            print "\t %s: %s " % (option.key, option.label)
        if default_option is not None:
            print "default (%s): %s\n" % (default_option.label,
                                          default_option.key)
        choice = raw_input("\nchoice number: ").strip()
        print "..."
    return choice


# form a connection...
args = get_args()
si = connect.SmartConnect(host=args.host, user=args.user, pwd=args.password,
                          port=args.port)

# doing this means you don't need to remember to disconnect your script/objects
atexit.register(connect.Disconnect, si)

# search the whole inventory tree recursively... a brutish but effective tactic
vm = None
entity_stack = si.content.rootFolder.childEntity
while entity_stack:
    entity = entity_stack.pop()

    if entity.name == args.name:
        vm = entity
        del entity_stack[0:len(entity_stack)]
    elif hasattr(entity, 'childEntity'):
        entity_stack.extend(entity.childEntity)
    elif isinstance(entity, vim.Datacenter):
        entity_stack.append(entity.vmFolder)

if not isinstance(vm, vim.VirtualMachine):
    print "could not find a virtual machine with the name %s" % args.name
    sys.exit(-1)

print "Found VirtualMachine: %s Name: %s" % (vm, vm.name)

if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
    # using time.sleep we just wait until the power off action
    # is complete. Nothing fancy here.
    print "reset the vm"
    task = vm.ResetVM_Task()
    while task.info.state not in [vim.TaskInfo.State.success,
                                  vim.TaskInfo.State.error]:
        time.sleep(1)
    print "resetting vm ..."


sys.exit(0)