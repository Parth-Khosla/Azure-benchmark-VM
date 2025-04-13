import subprocess
import json
from tabulate import tabulate

def fetch_resource_groups():
    """
    Fetches the list of resource groups using Azure CLI.
    Returns a dictionary of resource groups.
    """
    try:
        command = "az group list --output json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        resource_groups = json.loads(result.stdout)

        if not resource_groups:
            print("No resource groups found.")
            return {}

        headers = ["Option", "Name", "Location", "Provisioning State"]
        rows = []
        rg_details = {}

        for idx, rg in enumerate(resource_groups, 1):
            rows.append([idx, rg["name"], rg["location"], rg["properties"]["provisioningState"]])
            rg_details[str(idx)] = rg["name"]

        print("\nAvailable Resource Groups:")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        return rg_details

    except subprocess.CalledProcessError as e:
        print(f"Error fetching resource groups: {e.stderr}")
        return {}

def fetch_resources_in_group(resource_group):
    """
    Fetches all resources in a specific resource group.
    """
    try:
        command = f"az resource list --resource-group {resource_group} --output json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        resources = json.loads(result.stdout)

        if not resources:
            print(f"No resources found in resource group '{resource_group}'.")
            return []

        headers = ["Option", "Name", "Type", "Location"]
        rows = []
        resource_details = {}

        for idx, resource in enumerate(resources, 1):
            rows.append([idx, resource["name"], resource["type"], resource["location"]])
            resource_details[str(idx)] = resource

        print(f"\nResources in Resource Group '{resource_group}':")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        return resource_details

    except subprocess.CalledProcessError as e:
        print(f"Error fetching resources: {e.stderr}")
        return {}

def check_and_detach_nic(resource_name, resource_group):
    """
    Checks if a NIC is attached to any VM and detaches it before deletion.
    """
    try:
        # Check if the NIC is attached to a VM
        command = f"az network nic show --name {resource_name} --resource-group {resource_group} --output json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        nic_info = json.loads(result.stdout)

        # If the NIC is attached to a VM, detach it
        if "ipConfigurations" in nic_info and nic_info["ipConfigurations"]:
            print(f"NIC '{resource_name}' is attached to a VM. Detaching...")
            # This step involves disassociating the NIC (additional CLI commands may be needed for VM detachment)
            command = f"az network nic ip-config update --name ipconfig1 --nic-name {resource_name} --resource-group {resource_group} --remove ipConfigurations"
            subprocess.run(command, shell=True, check=True)
            print(f"NIC '{resource_name}' successfully detached.")
        else:
            print(f"NIC '{resource_name}' is not attached to any VM.")
    except subprocess.CalledProcessError as e:
        print(f"Error checking or detaching NIC: {e.stderr}")

def delete_resources(resources):
    """
    Deletes selected resources using Azure CLI with dependency checks.
    """
    for resource in resources:
        try:
            name = resource["name"]
            resource_type = resource["type"]
            resource_group = resource["resourceGroup"]

            # Perform checks and detach NICs before deletion
            if "Microsoft.Network/networkInterfaces" in resource_type:
                check_and_detach_nic(name, resource_group)

            # Delete the resource
            print(f"Deleting resource '{name}' of type '{resource_type}' in resource group '{resource_group}'...")
            command = f"az resource delete --name {name} --resource-group {resource_group} --resource-type {resource_type} --verbose"
            subprocess.run(command, shell=True, check=True)
            print(f"Resource '{name}' successfully deleted.")

        except subprocess.CalledProcessError as e:
            print(f"Error deleting resource: {e.stderr}")

def main():
    print("Azure Resource Management Script")
    print("=" * 30)

    # Fetch resource groups
    resource_groups = fetch_resource_groups()
    if not resource_groups:
        return

    rg_choice = input("\nSelect a resource group by number: ")
    resource_group = resource_groups.get(rg_choice)
    if not resource_group:
        print("Invalid resource group selection.")
        return

    # Fetch resources in the selected resource group
    resources = fetch_resources_in_group(resource_group)
    if not resources:
        return

    # Select resources to delete
    resource_choices = input("\nEnter the numbers of the resources to delete (comma-separated): ").split(",")
    selected_resources = [resources.get(choice.strip()) for choice in resource_choices if resources.get(choice.strip())]

    if not selected_resources:
        print("No valid resources selected for deletion.")
        return

    # Confirm deletion
    confirm = input(f"\nAre you sure you want to delete the selected resources? (yes/no): ")
    if confirm.lower() != "yes":
        print("Deletion canceled.")
        return

    # Delete selected resources
    delete_resources(selected_resources)

if __name__ == "__main__":
    main()
