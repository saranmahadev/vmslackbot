from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

from dotenv import dotenv_values

import random
import string

class VmCore:
    def __init__(self) -> None:
        self.credentials = dotenv_values("credentials.env")
        self.client = AzureCliCredential()
        self.subscription_id = self.credentials["SUBSCRIPTION_ID"]
        self.resource_client = ResourceManagementClient(self.client, self.subscription_id)
        self.network_client = NetworkManagementClient(self.client, self.subscription_id)
        self.compute_client = ComputeManagementClient(self.client, self.subscription_id)        


    # General functions
    def wordgen(self) -> str:
        """
        Generates a random word.
        """
        return ''.join(random.choice(string.ascii_lowercase) for i in range(15))

    def generate_password(self) -> str:
        """
        Generates a random password.
        Conditions:
            1) Contains an uppercase character
            2) Contains a lowercase character
            3) Contains a numeric digit
            4) Contains a special character
            5) Control characters are not allowed
        """
        password = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation) for i in range(12))
        conditions = [
            any(char.isupper() for char in password),
            any(char.islower() for char in password),
            any(char.isdigit() for char in password),
            any(char in string.punctuation for char in password),
            not any(char.isspace() for char in password)
        ]
        if all(conditions):
            return password
        else:
            return self.generate_password()

    # Resource Group functions    
    def check_resource_group_exists(self, group_name: str) -> bool:
        """
        Checks if a resource group exists.
        """        
        return self.resource_client.resource_groups.check_existence(group_name)

    def get_all_resource_groups(self) -> list:
        """
        Gets all resource groups.
        """
        return self.resource_client.resource_groups.list()

    def get_resource_group_poller(self, group_name: str):
        """
        Gets a resource group poller.
        """
        return self.resource_client.resource_groups.get(group_name)

    def delete_resource_group(self, group_name: str):
        """
        Deletes a resource group.
        """
        return self.resource_client.resource_groups.begin_delete(group_name)

    def create_resource_group(self, group_name: str, location: str) -> None:
        """
        Creates a resource group.
        """
        if self.check_resource_group_exists(group_name):
            print("Resource group already exists.")
        else:
            self.resource_client.resource_groups.create_or_update(
                group_name,
                {
                    "location": location
                }
            )            

    # Virtual Network Functions
    def get_virtual_network_poller(self, group_name: str, vnet_name: str):
        """
        Gets a virtual network poller.
        """
        return self.network_client.virtual_networks.get(group_name, vnet_name)

    def get_all_virtual_networks(self, group_name: str) -> list:
        """
        Gets all virtual networks.
        """
        return self.network_client.virtual_networks.list(group_name)

    def delete_virtual_network(self, group_name: str, vnet_name: str):
        """
        Deletes a virtual network.
        """
        return self.network_client.virtual_networks.begin_delete(
            group_name,
            vnet_name
        )

    def provision_virtual_network(self,
        group_name: str, vnet_name: str, location: str):
        """
        Creates a virtual network.
        """
        return self.network_client.virtual_networks.begin_create_or_update(
            group_name,
            vnet_name,
            {
                "location": location,       
                "address_space": {
                    "address_prefixes": ["10.0.0.0/16"]
                }
            }
        )
    

    # Subnet Functions
    def provision_subnet(self, 
        group_name: str, vnet_name: str, subnet_name: str, location: str):
        """
        Creates a subnet.
        """
        return self.network_client.subnets.begin_create_or_update(
            group_name,
            vnet_name,
            subnet_name,
            {
                "location": location,           
                "address_prefix": "10.0.0.0/24"
            }
        )
    
    # IP Address Functions
    def provision_ip_address(self, group_name: str,location: str):
        """
        Creates an IP address.
        """
        return self.network_client.public_ip_addresses.begin_create_or_update(
            group_name,
            self.wordgen()+"ip",
            {
                "location": location,
                "sku": {
                    "name": "Standard"
                },
                "public_ip_allocation_method": "Static",
                "public_ip_address_version": "IPv4"
            }
        )

    # NIC Functions
    def provision_nic(
        self, group_name: str, vnet_name: str, subnet_name: str, nic_name: str, 
        ipconfig_name: str,location: str):
        """
        Creates a NIC.
        """        
        self.create_resource_group(group_name, location)
        self.vpn_poller = self.provision_virtual_network(group_name, vnet_name, location).result()
        self.subnet_poller = self.provision_subnet(group_name, vnet_name, subnet_name, location).result()
        self.ip_address_poller = self.provision_ip_address(group_name, location).result()

        return self.network_client.network_interfaces.begin_create_or_update(
            group_name,
            nic_name,
            {
                "location": location,
                "ip_configurations": [
                    {
                        "name": ipconfig_name,
                        "subnet": {
                            "id": self.subnet_poller.id
                        },
                        "public_ip_address": {
                            "id": self.ip_address_poller.id
                        }
                    }
                ]
            }
        )
    
    # VM Functions
    def provision_vm(self, 
        group_name: str, vnet_name: str, subnet_name: str, nic_name: str, vm_name: str, 
        location: str,username: str) -> dict:
        """
        Creates a VM.
        """      
        self.nic_poller = self.provision_nic(
            group_name, vnet_name, subnet_name, nic_name, "ipconfig", location
        ).result()
        password = self.generate_password()
        
        self.vm_poller = self.compute_client.virtual_machines.begin_create_or_update(
            group_name,
            vm_name,
            {
                "location": location,
                "os_profile": {
                    "computer_name": vm_name,
                    "admin_username": username,
                    "admin_password": password
                },
                "hardware_profile": {
                    "vm_size": "Standard_DS1_v2"
                },
                "storage_profile": {
                    "image_reference": {
                        "publisher": "Canonical",
                        "offer": "UbuntuServer",
                        "sku": "16.04.0-LTS",
                        "version": "latest"
                    }
                },
                "network_profile": {
                    "network_interfaces": [
                        {
                            "id": self.nic_poller.id
                        }
                    ]
                },
            }
        )
        return {
            "vm_name": vm_name,
            "vm_id": self.vm_poller.id,
            "vm_location": location,
            "vm_size": "Standard_DS1_v2",
            "vm_username": username,
            "vm_password": password,
            "vm_public_ip": self.ip_address_poller.ip_address,
            "vm_private_ip": self.nic_poller.ip_configurations[0].private_ip_address            
        }

    def delete_vm(self, group_name: str, vm_name: str):
        """
        Deletes a VM.
        """
        return self.compute_client.virtual_machines.begin_delete(
            group_name,
            vm_name
        )

    def stop_vm(self, group_name: str, vm_name: str):
        """
        Stops a VM.
        """
        return self.compute_client.virtual_machines.begin_power_off(
            group_name,
            vm_name
        )

    def start_vm(self, group_name: str, vm_name: str):
        """
        Starts a VM.
        """
        return self.compute_client.virtual_machines.begin_start(
            group_name,
            vm_name
        )           


    def vm_status(self, group_name: str, vm_name: str):
        """
        Gets the status of a VM.
        """
        return self.compute_client.virtual_machines.get(
            group_name,
            vm_name
        )

    def list_all_vms(self, group_name: str):
        """
        Lists all instances in a resource group.
        """
        return self.compute_client.virtual_machines.list(group_name)
    

