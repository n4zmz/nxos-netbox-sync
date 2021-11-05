import pynetbox
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# import ipaddress

netbox_token = os.getenv("NETBOX_TOKEN")
netbox_url = os.getenv("NETBOX_URL")
switch_name = os.getenv("SWITCH_HOSTNAME")

# site_name = os.getenv("NETBOX_SITE")
# tenant_name = os.getenv("NETBOX_TENANT")

netbox = pynetbox.api(netbox_url, token=netbox_token)
netbox.http_session.verify = False
device = netbox.dcim.devices.get(name=switch_name)


def interfaces_sot(): 
    interfaces = netbox.dcim.interfaces.filter(device_id=device.id)
    # for interface in interfaces:
    #     interface.ip_addresses = netbox.ipam.ip_addresses.filter(
    #         interface_id=interface.id
    #     )
    #     for ip_address in interface.ip_addresses:
    #         ip_address.ip = ipaddress.ip_address(
    #             ip_address.address.split("/")[0]
    #         )
    #         ip_address.network = ipaddress.ip_network(
    #             ip_address.address, strict=False
    #         )

    return list(interfaces)


def vlans_sot(): 
    vlans = netbox.ipam.vlans.filter(site_id=device.site.id)
    return list(vlans)
