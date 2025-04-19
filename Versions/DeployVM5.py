import os
import json
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
from tabulate import tabulate

def get_credentials():
    return AzureCliCredential()

def validate_vm_name(name):
    valid_name = ''.join(c for c in name if c.isalnum() or c == '-')
    valid_name = valid_name[:15]
    
    if valid_name.isnumeric() or not valid_name[0].isalpha():
        valid_name = 'vm-' + valid_name
    
    return valid_name

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

def list_regions(credential, subscription_id):
    subscription_client = SubscriptionClient(credential)
    locations = list(subscription_client.subscriptions.list_locations(subscription_id))
    
    headers = ["Option", "Name", "Display Name"]
    rows = []
    
    for idx, location in enumerate(locations, 1):
        rows.append([str(idx), location.name, location.display_name])
    
    print("\nAvailable Regions:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return {str(idx): location.name for idx, location in enumerate(locations, 1)}

def list_common_vm_sizes(credential, subscription_id, location):
    # Define most common VM sizes
    common_sizes = [
        {
            'name': 'Standard_B2s',
            'cores': 2,
            'memory': 4,
            'disks': 4
        },
        {
            'name': 'Standard_D2s_v3',
            'cores': 2,
            'memory': 8,
            'disks': 4
        },
        {
            'name': 'Standard_D4s_v3',
            'cores': 4,
            'memory': 16,
            'disks': 8
        },
        {
            'name': 'Standard_D8s_v3',
            'cores': 8,
            'memory': 32,
            'disks': 16
        },
        {
            'name': 'Standard_E2s_v3',
            'cores': 2,
            'memory': 16,
            'disks': 4
        },
        {
            'name': 'Standard_E4s_v3',
            'cores': 4,
            'memory': 32,
            'disks': 8
        },
        {
            'name': 'Standard_F2s_v2',
            'cores': 2,
            'memory': 4,
            'disks': 4
        },
        {
            'name': 'Standard_F4s_v2',
            'cores': 4,
            'memory': 8,
            'disks': 8
        },
        {
            'name': 'Standard_B4ms',
            'cores': 4,
            'memory': 16,
            'disks': 8
        },
        {
            'name': 'Standard_B8ms',
            'cores': 8,
            'memory': 32,
            'disks': 16
        }
    ]
    
    headers = ["Option", "Size", "vCPUs", "Memory (GB)", "Max Data Disks"]
    rows = []
    
    for idx, size in enumerate(common_sizes, 1):
        rows.append([
            str(idx),
            size['name'],
            size['cores'],
            size['memory'],
            size['disks']
        ])
    
    print("\nCommon VM Sizes:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return {str(idx): size['name'] for idx, size in enumerate(common_sizes, 1)}

def list_common_vm_images():
    # Define most common VM images
    common_images = [
        # Ubuntu Images
        {
            'publisher': 'Canonical',
            'offer': 'UbuntuServer',
            'sku': '18.04-LTS',
            'version': 'latest',
            'description': 'Ubuntu Server 18.04 LTS'
        },
        {
            'publisher': 'Canonical',
            'offer': 'UbuntuServer',
            'sku': '20.04-LTS',
            'version': 'latest',
            'description': 'Ubuntu Server 20.04 LTS'
        },
        {
            'publisher': 'Canonical',
            'offer': '0001-com-ubuntu-server-focal',
            'sku': '20_04-lts-gen2',
            'version': 'latest',
            'description': 'Ubuntu Server 20.04 LTS Gen2'
        },
        # Windows Images
        {
            'publisher': 'MicrosoftWindowsServer',
            'offer': 'WindowsServer',
            'sku': '2019-Datacenter',
            'version': 'latest',
            'description': 'Windows Server 2019 Datacenter'
        },
        {
            'publisher': 'MicrosoftWindowsServer',
            'offer': 'WindowsServer',
            'sku': '2022-Datacenter',
            'version': 'latest',
            'description': 'Windows Server 2022 Datacenter'
        },
        {
            'publisher': 'MicrosoftWindowsServer',
            'offer': 'WindowsServer',
            'sku': '2019-Datacenter-Core',
            'version': 'latest',
            'description': 'Windows Server 2019 Datacenter Core'
        },
        # Linux Images
        {
            'publisher': 'RedHat',
            'offer': 'RHEL',
            'sku': '8-gen2',
            'version': 'latest',
            'description': 'Red Hat Enterprise Linux 8 Gen2'
        },
        {
            'publisher': 'SUSE',
            'offer': 'sles-15-sp3',
            'sku': 'gen2',
            'version': 'latest',
            'description': 'SUSE Linux Enterprise Server 15 SP3'
        },
        {
            'publisher': 'debian',
            'offer': 'debian-11',
            'sku': '11-gen2',
            'version': 'latest',
            'description': 'Debian 11 Gen2'
        },
        {
            'publisher': 'OpenLogic',
            'offer': 'CentOS',
            'sku': '8_5-gen2',
            'version': 'latest',
            'description': 'CentOS 8.5 Gen2'
        }
    ]
    
    headers = ["Option", "Description", "Publisher"]
    rows = []
    
    for idx, image in enumerate(common_images, 1):
        rows.append([
            str(idx),
            image['description'],
            image['publisher']
        ])
    
    print("\nCommon VM Images:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return {str(idx): image for idx, image in enumerate(common_images, 1)}

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
            vm.id.split('/')[4],
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
    resource_client = ResourceManagementClient(credential, subscription_id)
    network_client = NetworkManagementClient(credential, subscription_id)
    compute_client = ComputeManagementClient(credential, subscription_id)

    computer_name = validate_vm_name(vm_name)

    print(f"Creating Resource Group '{resource_group_name}'...")
    resource_client.resource_groups.create_or_update(
        resource_group_name,
        {"location": location}
    )

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

    print(f"Creating VM '{vm_name}'...")
    vm_parameters = {
        'location': location,
        'hardware_profile': {'vm_size': vm_size},
        'storage_profile': {
            'image_reference': {
                'publisher': vm_image['publisher'],
                'offer': vm_image['offer'],
                'sku': vm_image['sku'],
                'version': vm_image['version']
            },
            'os_disk': {
                'name': f'{vm_name}-disk',
                'caching': 'ReadWrite',
                'create_option': 'FromImage',
                'managed_disk': {'storage_account_type': 'Standard_LRS'}
            }
        },
        'os_profile': {
            'computer_name': computer_name,
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

def deploy_to_regions(credential, subscription_id, regions, vm_config):
    for region in regions:
        region_rg_name = f"{vm_config['resource_group_name']}-{region}"
        region_vm_name = f"{vm_config['vm_name']}-{region}"
        
        print(f"\nDeploying to region: {region}")
        create_infrastructure(
            credential=credential,
            subscription_id=subscription_id,
            resource_group_name=region_rg_name,
            location=region,
            vm_name=region_vm_name,
            vm_size=vm_config['vm_size'],
            vm_image=vm_config['vm_image']
        )

def main():
    print("Azure Multi-Region VM Deployment Script")
    print("=" * 40)

    credential = get_credentials()
    
    subscriptions_dict = list_subscriptions(credential)
    if not subscriptions_dict:
        print("No subscriptions found. Please check your Azure login.")
        return
        
    sub_choice = input("\nSelect subscription (enter number): ")
    subscription_id = subscriptions_dict.get(sub_choice)
    if not subscription_id:
        print("Invalid subscription selection.")
        return

    list_virtual_machines(credential, subscription_id)
    
    print("\n=== Base VM Configuration ===")
    
    vm_name_base = input("\nEnter base VM name: ")
    resource_group_base = input("Enter base resource group name: ")
    
    regions_dict = list_regions(credential, subscription_id)
    if not regions_dict:
        print("No regions available.")
        return
        
    vm_sizes_dict = list_common_vm_sizes(credential, subscription_id, list(regions_dict.values())[0])
    vm_size_choice = input("\nSelect VM size (enter number): ")
    vm_size = vm_sizes_dict.get(vm_size_choice)
    if not vm_size:
        print("Invalid VM size selection.")
        return

    vm_images_dict = list_common_vm_images()
    vm_image_choice = input("\nSelect VM image (enter number): ")
    vm_image = vm_images_dict.get(vm_image_choice)
    if not vm_image:
        print("Invalid VM image selection.")
        return

    print("\nSelect regions (comma-separated numbers, e.g., 1,2,3): ")
    region_choices = input().split(',')
    selected_regions = [regions_dict.get(choice.strip()) for choice in region_choices]
    selected_regions = [r for r in selected_regions if r]
    
    if not selected_regions:
        print("No valid regions selected.")
        return

    vm_config = {
        'vm_name': vm_name_base,
        'resource_group_name': resource_group_base,
        'vm_size': vm_size,
        'vm_image': vm_image
    }

    deploy_to_regions(credential, subscription_id, selected_regions, vm_config)
    
    print("\nMulti-region deployment completed!")

if __name__ == "__main__":
    main()