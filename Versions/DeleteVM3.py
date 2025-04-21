import subprocess
import json
from tabulate import tabulate
from time import time

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

def delete_resource_group(resource_group):
    """
    Deletes an entire resource group using Azure CLI and measures the total time taken.
    """
    try:
        print(f"Deleting resource group '{resource_group}' and all its resources...")
        start_time = time()

        # Delete the resource group and wait for completion
        command = f"az group delete --name {resource_group} --yes"
        subprocess.run(command, shell=True, check=True)

        end_time = time()
        total_time = end_time - start_time
        print(f"Resource group '{resource_group}' successfully deleted.")
        print(f"Total time taken for deletion: {total_time:.2f} seconds.")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting resource group: {e.stderr}")

def delete_resources(resources):
    """
    Deletes selected resources using Azure CLI with dependency checks.
    """
    for resource in resources:
        try:
            name = resource["name"]
            resource_type = resource["type"]
            resource_group = resource["resourceGroup"]

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

    # Ask user if they want to delete the entire resource group
    action = input(f"\nWould you like to delete the entire Resource Group '{resource_group}'? (yes/no): ")
    if action.lower() == "yes":
        delete_resource_group(resource_group)
        return

    # Fetch resources in the selected resource group
    resources = fetch_resources_in_group(resource_group)
    if not resources:
        return

    # Display deletion order guidance
    print("\nImportant Info:")
    print("Please remove resources in the following order to avoid dependency issues:")
    print("1. Virtual Machines (VM)")
    print("2. Disks")
    print("3. Network Interfaces (NIC)")
    print("4. Virtual Networks (V-net)")
    print("5. IP Addresses")

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
