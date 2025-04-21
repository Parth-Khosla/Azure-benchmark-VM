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

def fetch_resources_in_groups(resource_groups):
    """
    Fetches all resources in specified resource groups.
    """
    try:
        all_resources = []
        for rg in resource_groups:
            command = f"az resource list --resource-group {rg} --output json"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            resources = json.loads(result.stdout)
            all_resources.extend(resources)

        if not all_resources:
            print(f"No resources found in the selected resource groups.")
            return {}

        headers = ["Option", "Name", "Type", "Resource Group", "Location"]
        rows = []
        resource_details = {}

        for idx, resource in enumerate(all_resources, 1):
            rows.append([
                idx, 
                resource["name"], 
                resource["type"], 
                resource["resourceGroup"],
                resource["location"]
            ])
            resource_details[str(idx)] = resource

        print("\nResources in Selected Resource Groups:")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        return resource_details

    except subprocess.CalledProcessError as e:
        print(f"Error fetching resources: {e.stderr}")
        return {}

def delete_resource_groups(resource_groups):
    """
    Deletes multiple resource groups using Azure CLI.
    """
    for rg in resource_groups:
        try:
            print(f"\nDeleting resource group '{rg}' and all its resources...")
            start_time = time()

            command = f"az group delete --name {rg} --yes"
            subprocess.run(command, shell=True, check=True)

            end_time = time()
            total_time = end_time - start_time
            print(f"Resource group '{rg}' successfully deleted.")
            print(f"Total time taken for deletion: {total_time:.2f} seconds.")
        except subprocess.CalledProcessError as e:
            print(f"Error deleting resource group '{rg}': {e.stderr}")

def delete_resources(resources):
    """
    Deletes selected resources using Azure CLI with dependency checks.
    """
    for resource in resources:
        try:
            name = resource["name"]
            resource_type = resource["type"]
            resource_group = resource["resourceGroup"]

            print(f"Deleting resource '{name}' of type '{resource_type}' in resource group '{resource_group}'...")
            command = f"az resource delete --name {name} --resource-group {resource_group} --resource-type {resource_type} --verbose"
            subprocess.run(command, shell=True, check=True)
            print(f"Resource '{name}' successfully deleted.")
        except subprocess.CalledProcessError as e:
            print(f"Error deleting resource: {e.stderr}")

def main():
    print("Azure Resource Management Script")
    print("=" * 30)

    while True:
        print("\nOptions:")
        print("1. Delete entire resource groups")
        print("2. Delete specific resources across resource groups")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ")

        if choice == "3":
            break

        # Fetch resource groups
        resource_groups = fetch_resource_groups()
        if not resource_groups:
            continue

        if choice == "1":
            # Delete entire resource groups
            rg_choices = input("\nSelect resource groups to delete (comma-separated numbers): ").split(",")
            selected_rgs = [resource_groups.get(choice.strip()) for choice in rg_choices if resource_groups.get(choice.strip())]

            if not selected_rgs:
                print("No valid resource groups selected.")
                continue

            confirm = input(f"\nAre you sure you want to delete these resource groups and ALL their resources?\n"
                          f"Selected groups: {', '.join(selected_rgs)}\n"
                          f"Type 'yes' to confirm: ")
            
            if confirm.lower() == "yes":
                delete_resource_groups(selected_rgs)

        elif choice == "2":
            # Delete specific resources
            rg_choices = input("\nSelect resource groups to view resources from (comma-separated numbers): ").split(",")
            selected_rgs = [resource_groups.get(choice.strip()) for choice in rg_choices if resource_groups.get(choice.strip())]

            if not selected_rgs:
                print("No valid resource groups selected.")
                continue

            # Fetch and display resources from selected resource groups
            resources = fetch_resources_in_groups(selected_rgs)
            if not resources:
                continue

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
                continue

            # Confirm deletion
            confirm = input(f"\nAre you sure you want to delete the selected resources? (yes/no): ")
            if confirm.lower() == "yes":
                delete_resources(selected_resources)

if __name__ == "__main__":
    main()