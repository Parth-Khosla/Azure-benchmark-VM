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
    # Remove invalid characters and ensure it's not longer than 15 characters
    valid_name = ''.join(c for c in name if c.isalnum() or c == '-')
    valid_name = valid_name[:15]
    
    # Ensure it's not entirely numeric and starts with a letter
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

def list_vm_sizes(credential, subscription_id, location):
    compute_client = ComputeManagementClient(credential, subscription_id)
    vm_sizes = list(compute_client.virtual_machine_sizes.list(location))
    
    headers = ["Option", "Size", "vCPUs", "Memory (GB)", "Max Data Disks"]
    rows = []
    
    for idx, size in enumerate(vm_sizes, 1):
        rows.append([
            str(idx),
            size.name,
            size.number_of_cores,
            size.memory_in_mb / 1024,
            size.max_data_disk_count
        ])
    
    print("\nAvailable VM Sizes:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return {str(idx): size.name for idx, size in enumerate(vm_sizes, 1)}

def list_vm_images(credential, subscription_id, location):
    compute_client = ComputeManagementClient(credential, subscription_id)
    
    # Get popular publishers
    publishers = [
        'Canonical',
        'MicrosoftWindowsServer',
        'RedHat',
        'SUSE',
        'debian'
    ]
    
    images = []
    for publisher in publishers:
        try:
            offers = compute_client.virtual_machine_images.list_offers(
                location,
                publisher
            )
            
            for offer in offers:
                skus = compute_client.virtual_machine_images.list_skus(
                    location,
                    publisher,
                    offer.name
                )
                
                for sku in skus:
                    images.append({
                        'publisher': publisher,
                        'offer': offer.name,
                        'sku': sku.name,
                        'version': 'latest'
                    })
        except Exception as e:
            continue
    
    headers = ["Option", "Publisher", "Offer", "SKU"]
    rows = []
    
    for idx, image in enumerate(images, 1):
        rows.append([
            str(idx),
            image['publisher'],
            image['offer'],
            image['sku']
        ])
    
    print("\nAvailable VM Images:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return {str(idx): image for idx, image in enumerate(images, 1)}

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
    # Initialize clients
    resource_client = ResourceManagementClient(credential, subscription_id)
    network_client = NetworkManagementClient(credential, subscription_id)
    compute_client = ComputeManagementClient(credential, subscription_id)

    # Validate and format VM name
    computer_name = validate_vm_name(vm_name)

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
    """
    Deploy the same VM configuration across multiple regions
    
    Args:
        credential: Azure credentials
        subscription_id: Target subscription ID
        regions: List of region names to deploy to
        vm_config: Dictionary containing VM configuration
    """
    for region in regions:
        # Create region-specific names
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
    
    # Get subscription
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
    
    # Get base configuration first
    print("\n=== Base VM Configuration ===")
    
    # Get VM name base
    vm_name_base = input("\nEnter base VM name: ")
    
    # Get base resource group name
    resource_group_base = input("Enter base resource group name: ")
    
    # Get regions first to use for VM size listing
    regions_dict = list_regions(credential, subscription_id)
    if not regions_dict:
        print("No regions available.")
        return
        
    # Select VM size using first region (sizes are generally consistent across regions)
    vm_sizes_dict = list_vm_sizes(credential, subscription_id, list(regions_dict.values())[0])
    vm_size_choice = input("\nSelect VM size (enter number): ")
    vm_size = vm_sizes_dict.get(vm_size_choice)
    if not vm_size:
        print("Invalid VM size selection.")
        return

    # Select VM image
    vm_images_dict = list_vm_images(credential, subscription_id, list(regions_dict.values())[0])
    vm_image_choice = input("\nSelect VM image (enter number): ")
    vm_image = vm_images_dict.get(vm_image_choice)
    if not vm_image:
        print("Invalid VM image selection.")
        return

    # Select target regions
    print("\nSelect regions (comma-separated numbers, e.g., 1,2,3): ")
    region_choices = input().split(',')
    selected_regions = [regions_dict.get(choice.strip()) for choice in region_choices]
    selected_regions = [r for r in selected_regions if r]  # Remove any invalid selections
    
    if not selected_regions:
        print("No valid regions selected.")
        return

    # Create VM configuration dictionary
    vm_config = {
        'vm_name': vm_name_base,
        'resource_group_name': resource_group_base,
        'vm_size': vm_size,
        'vm_image': vm_image
    }

    # Deploy to all selected regions
    deploy_to_regions(credential, subscription_id, selected_regions, vm_config)
    
    print("\nMulti-region deployment completed!")

if __name__ == "__main__":
    main()
