import os
import json
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
from tabulate import tabulate

# Existing VM configurations
VM_IMAGES = {
    '1': {
        'publisher': 'Canonical',
        'offer': 'UbuntuServer',
        'sku': '18.04-LTS',
        'version': 'latest'
    },
    '2': {
        'publisher': 'MicrosoftWindowsServer',
        'offer': 'WindowsServer',
        'sku': '2019-Datacenter',
        'version': 'latest'
    },
    '3': {
        'publisher': 'Debian',
        'offer': 'debian-10',
        'sku': '10',
        'version': 'latest'
    }
}

VM_SIZES = {
    '1': 'Standard_B1s',  # 1 vCPU, 1 GB RAM
    '2': 'Standard_B2s',  # 2 vCPU, 4 GB RAM
    '3': 'Standard_D2s_v3'  # 2 vCPU, 8 GB RAM
}

# Azure regions with friendly names
REGIONS = {
    '1': ('eastus', 'East US'),
    '2': ('westus', 'West US'),
    '3': ('northeurope', 'North Europe'),
    '4': ('westeurope', 'West Europe'),
    '5': ('southeastasia', 'Southeast Asia'),
    '6': ('eastasia', 'East Asia'),
    '7': ('centralus', 'Central US'),
    '8': ('westus2', 'West US 2'),
    '9': ('ukwest', 'UK West'),
    '10': ('uksouth', 'UK South')
}

def print_options(options_dict, title):
    print(f"\n{title}:")
    headers = ["Option", "Details"]
    rows = []
    
    for key, value in options_dict.items():
        if isinstance(value, dict):
            details = f"{value['publisher']} - {value['offer']} {value['sku']}"
        elif isinstance(value, tuple):
            details = f"{value[1]} ({value[0]})"
        else:
            details = value
        rows.append([key, details])
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))

def get_credentials():
    return AzureCliCredential()

def list_subscriptions(credential):
    subscription_client = SubscriptionClient(credential)
    subscriptions = list(subscription_client.subscriptions.list())
    
    headers = ["Option", "Subscription ID", "Name", "State"]
    rows = []
    
    for idx, sub in enumerate(subscriptions, 1):
        rows.append([str(idx), sub.subscription_id, sub.display_name, sub.state])
    
    print("\nAvailable Subscriptions:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return {str(idx): sub.subscription_id for idx, sub in enumerate(subscriptions, 1)}

def list_resource_groups(credential, subscription_id):
    resource_client = ResourceManagementClient(credential, subscription_id)
    resource_groups = list(resource_client.resource_groups.list())
    
    headers = ["Option", "Name", "Location", "Provisioning State"]
    rows = []
    
    for idx, rg in enumerate(resource_groups, 1):
        rows.append([str(idx), rg.name, rg.location, rg.properties.provisioning_state])
    
    print("\nExisting Resource Groups:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return {str(idx): rg.name for idx, rg in enumerate(resource_groups, 1)}

def list_virtual_machines(credential, subscription_id):
    compute_client = ComputeManagementClient(credential, subscription_id)
    vms = list(compute_client.virtual_machines.list_all())
    
    headers = ["Name", "Resource Group", "Location", "Size", "State"]
    rows = []
    
    for vm in vms:
        rows.append([
            vm.name,
            vm.id.split('/')[4],  # Extract resource group from ID
            vm.location,
            vm.hardware_profile.vm_size,
            vm.provisioning_state
        ])
    
    print("\nExisting Virtual Machines:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

def create_infrastructure(
    credential,
    subscription_id,
    resource_group_name,
    location,
    vm_name,
    vm_size,
    vm_image
):
    # Initialize clients
    resource_client = ResourceManagementClient(credential, subscription_id)
    network_client = NetworkManagementClient(credential, subscription_id)
    compute_client = ComputeManagementClient(credential, subscription_id)

    # Create resource group
    print(f"Creating Resource Group '{resource_group_name}'...")
    resource_client.resource_groups.create_or_update(
        resource_group_name,
        {"location": location}
    )

    # Create VNet and Subnet
    vnet_name = f"{vm_name}-vnet"
    subnet_name = f"{vm_name}-subnet"
    ip_name = f"{vm_name}-ip"
    nic_name = f"{vm_name}-nic"

    print("Creating VNet and Subnet...")
    network_client.virtual_networks.begin_create_or_update(
        resource_group_name,
        vnet_name,
        {
            'location': location,
            'address_space': {'address_prefixes': ['10.0.0.0/16']},
            'subnets': [{'name': subnet_name, 'address_prefix': '10.0.0.0/24'}]
        }
    ).result()

    subnet = network_client.subnets.get(resource_group_name, vnet_name, subnet_name)

    # Create Public IP
    print("Creating Public IP...")
    public_ip = network_client.public_ip_addresses.begin_create_or_update(
        resource_group_name,
        ip_name,
        {
            'location': location,
            'sku': {'name': 'Basic'},
            'public_ip_allocation_method': 'Dynamic',
            'public_ip_address_version': 'IPV4'
        }
    ).result()

    # Create NIC
    print("Creating Network Interface...")
    nic = network_client.network_interfaces.begin_create_or_update(
        resource_group_name,
        nic_name,
        {
            'location': location,
            'ip_configurations': [{
                'name': 'ipconfig1',
                'subnet': {'id': subnet.id},
                'public_ip_address': {'id': public_ip.id}
            }]
        }
    ).result()

    # Create VM
    print(f"Creating VM '{vm_name}'...")
    vm_parameters = {
        'location': location,
        'hardware_profile': {'vm_size': vm_size},
        'storage_profile': {
            'image_reference': vm_image,
            'os_disk': {
                'name': f'{vm_name}-disk',
                'caching': 'ReadWrite',
                'create_option': 'FromImage',
                'managed_disk': {'storage_account_type': 'Standard_LRS'}
            }
        },
        'os_profile': {
            'computer_name': vm_name,
            'admin_username': 'azureuser',
            'admin_password': 'Password123!'  # In production, use secure password handling
        },
        'network_profile': {
            'network_interfaces': [{'id': nic.id}]
        }
    }

    compute_client.virtual_machines.begin_create_or_update(
        resource_group_name,
        vm_name,
        vm_parameters
    ).result()

    print(f"\nVM '{vm_name}' has been successfully created!")

def main():
    print("Azure VM Deployment Script")
    print("=" * 30)

    # Get credentials
    credential = get_credentials()
    
    # List and select subscription
    subscriptions_dict = list_subscriptions(credential)
    if not subscriptions_dict:
        print("No subscriptions found. Please check your Azure login.")
        return
        
    sub_choice = input("\nSelect subscription (enter number): ")
    subscription_id = subscriptions_dict.get(sub_choice)
    if not subscription_id:
        print("Invalid subscription selection.")
        return

    # List existing VMs
    list_virtual_machines(credential, subscription_id)
    
    # Select region
    print_options(REGIONS, "Available Regions")
    region_choice = input("\nSelect region (enter number): ")
    region = REGIONS.get(region_choice)
    if not region:
        print("Invalid region selection.")
        return
    location = region[0]  # Use the region code, not the friendly name

    # List existing resource groups and option to create new
    existing_rgs = list_resource_groups(credential, subscription_id)
    print("\nResource Group Options:")
    print("1. Use existing resource group")
    print("2. Create new resource group")
    rg_option = input("\nSelect option (1 or 2): ")
    
    if rg_option == "1":
        if not existing_rgs:
            print("No existing resource groups found. Creating new one.")
            resource_group_name = input("Enter new resource group name: ")
        else:
            rg_choice = input("Select resource group (enter number): ")
            resource_group_name = existing_rgs.get(rg_choice)
            if not resource_group_name:
                print("Invalid resource group selection.")
                return
    else:
        resource_group_name = input("Enter new resource group name: ")
    
    # Get VM name
    vm_name = input("\nEnter VM name: ")

    # Select VM size
    print_options(VM_SIZES, "Available VM Sizes")
    vm_size_choice = input("\nSelect VM size (enter number): ")
    vm_size = VM_SIZES.get(vm_size_choice)

    # Select VM image
    print_options(VM_IMAGES, "Available VM Images")
    vm_image_choice = input("\nSelect VM image (enter number): ")
    vm_image = VM_IMAGES.get(vm_image_choice)

    if not all([vm_size, vm_image]):
        print("Invalid VM size or image selection.")
        return
    
    # Create infrastructure
    create_infrastructure(
        credential,
        subscription_id,
        resource_group_name,
        location,
        vm_name,
        vm_size,
        vm_image
    )

if __name__ == "__main__":
    main()