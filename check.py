#!/usr/bin/env python3

from __future__ import absolute_import

import utils.get_from_pyats as pyats
import utils.get_from_netbox as netbox
import utils.tests as tests
from utils.webex_teams import notify_team, fail_notification
from utils.message_templates import message_vlan_exist_template, message_interface_enabled_template, message_interface_description_template, message_interface_mode_template, message_interface_vlan_template
from time import sleep

import sys
import os
import os.path

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__version__ = "1.0.0"

def main(argv=None):
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_desc = program_name+" Check device against NetBox"

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_desc, formatter_class=RawDescriptionHelpFormatter)
        optional = parser._action_groups.pop()
        required = parser.add_argument_group("required arguments")

        optional.add_argument("-version", action="version", version="%(prog)s {version}".format(version=__version__))
        optional.add_argument("-debug", action="store_const", const="debug", help="enable debugging")
        optional.add_argument("-single", action="store_const", const="single", help="single pass")
#        optional.add_argument("-default", const="default", nargs='?', help="Default: %(default)s", default="Hello")
        optional.add_argument("-device", const="device", nargs='?', help="Default: %(default)s", default=os.getenv("SWITCH_HOSTNAME"))
        optional.add_argument("-testbed", const="testbed", nargs='?', help="Default: %(default)s", default="testbed.yml")

#        required.add_argument("-plan-file", const="plan_file", required=True, type=str, nargs='?', help="input plan file" )
#        required.add_argument("-out-file", const="out_file", required=True, type=str, nargs='?', help="output plan file" )
#        required.add_argument("-server", const="server", required=True, choices=["prd", "uat"], type=str, nargs='?', help="server type" )
#        required.add_argument("-asn", const="asn", required=True, type=str, nargs='?', help="asn" )

        parser._action_groups.append(optional)
        # Process arguments
        args = parser.parse_args()

    except Exception as e:
        print("%s" % (str(e)))

    my_name = pyats.device.hostname
    my_info = pyats.platform_info()

    # Say hello to room
    m = notify_team(f"Device {my_name} checking in.")

    # Continually check Netbox and test
    while True:
        print("Retrieving current status from device with pyATS")
        pyats_interfaces = pyats.interfaces_current()
        pyats_vlans = pyats.vlans_current()

        print("Looking up intended state for device from Netbox")
        netbox_interfaces = netbox.interfaces_sot()
        netbox_vlans = netbox.vlans_sot()

        # TEST: VLANs Exist on Switch
        print("Running tests to see if VLANs from Netbox are configured")
        vlan_exist_test = tests.verify_vlans_exist(netbox_vlans, pyats_vlans)
        m = fail_notification(vlan_exist_test["FAIL"], message_vlan_exist_template)

        # TEST: Interface Enabled Status 
        print("Running interface enabled test")
        interface_enabled_test = tests.verify_interface_enabled(netbox_interfaces, pyats_interfaces)
        m = fail_notification(interface_enabled_test["FAIL"], message_interface_enabled_template)

        # TEST: Interface Descriptions
        print("Running interface description test")
        interface_description_test = tests.verify_interface_descriptions(netbox_interfaces, pyats_interfaces)
        m = fail_notification(interface_description_test["FAIL"], message_interface_description_template)

        # TEST: Interface Modes 
        print("Running interface mode test")
        interface_mode_test = tests.verify_interface_mode(netbox_interfaces, pyats_interfaces)
        m = fail_notification(interface_mode_test["FAIL"], message_interface_mode_template)

        # TEST: Interface VLANs 
        print("Running interface vlan test")
        interface_vlan_test = tests.verify_interface_vlans(netbox_interfaces, pyats_interfaces, pyats_vlans)
        m = fail_notification(interface_vlan_test["FAIL"], message_interface_vlan_template)

        if args.debug:
            exit(0)

        # Fixes 
        # VLAN Configurations 
        if len(vlan_exist_test["FAIL"]) > 0: 
            vlan_configuration = pyats.vlans_configure(vlan_exist_test["FAIL"])
            m = notify_team(f"I am updating my VLAN Configuration.")

        # Interface Descriptions 
        if len(interface_enabled_test["FAIL"]) > 0: 
            interface_enable_configuration = pyats.interface_enable_state_configure(interface_enabled_test["FAIL"])
            m = notify_team(f"I am updating my Interface enabled states.")

        # Interface Descriptions 
        if len(interface_description_test["FAIL"]) > 0: 
            interface_description_configuration = pyats.interface_description_configure(interface_description_test["FAIL"])
            m = notify_team(f"I am updating my Interface Descriptions.")

        # Switchport Configurations 
        if len(interface_mode_test["FAIL"]) > 0 or len(interface_vlan_test["FAIL"]) > 0: 
            switchport_configuration = pyats.interface_switchport_configure(interface_mode_test["FAIL"])
            switchport_configuration = pyats.interface_switchport_configure(interface_vlan_test["FAIL"])
            m = notify_team(f"I am updating my Interface switchport configurations.")

        if args.single:
            sys.exit(0)

        # Wait 10 seconds and check again
        sleep(10)

if __name__ == "__main__":
    main()
    sys.exit(0)

