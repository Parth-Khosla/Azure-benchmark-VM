import json
import socket
import time
import os
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.subscription import SubscriptionClient
from tabulate import tabulate

def measure_tcp_latency(ip, ports=[22, 3389], timeout=2):
    for port in ports:
        try:
            start = time.time()
            with socket.create_connection((ip, port), timeout=timeout):
                latency = (time.time() - start) * 1000
                return round(latency, 2), port
        except (socket.timeout, ConnectionRefusedError, OSError):
            continue
    return None, None

def log_latency(vm_name, location, ip, port_used, latency_ms):
    entry = {
        "vm_name": vm_name,
        "location": location,
        "ip": ip,
        "port_used": port_used,
        "latency_ms": latency_ms
    }

    log_file = "latency_log.json"
    try:
        with open(log_file, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(entry)

    with open(log_file, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ {vm_name} @ {ip} (port {port_used}) latency: {latency_ms:.2f} ms")

def main():
    credential = AzureCliCredential()

    # Step 1: List subscriptions
    sub_client = SubscriptionClient(credential)
    subscriptions = list(sub_client.subscriptions.list())

    print("\n📋 Available Subscriptions:")
    sub_table = [[str(i+1), sub.subscription_id, sub.display_name, sub.state] for i, sub in enumerate(subscriptions)]
    print(tabulate(sub_table, headers=["#", "Subscription ID", "Name", "State"], tablefmt="grid"))

    sub_choice = input("\nEnter the number of the subscription to use: ").strip()
    try:
        subscription_id = subscriptions[int(sub_choice)-1].subscription_id
    except:
        print("❌ Invalid choice.")
        return

    compute_client = ComputeManagementClient(credential, subscription_id)
    network_client = NetworkManagementClient(credential, subscription_id)

    print("\n🔍 Fetching all VMs in subscription...")
    vms = list(compute_client.virtual_machines.list_all())

    if not vms:
        print("📭 No VMs found.")
        return

    vm_table = []
    for i, vm in enumerate(vms):
        vm_table.append([
            str(i+1),
            vm.name,
            vm.location,
            vm.hardware_profile.vm_size,
            vm.id.split("/")[4]  # Resource group
        ])

    print("\n📋 Available VMs:")
    print(tabulate(vm_table, headers=["#", "VM Name", "Location", "Size", "Resource Group"], tablefmt="grid"))

    selected = input("\nEnter VM numbers to check latency (comma-separated, e.g., 1,3,4): ").split(",")
    selected = [int(i.strip()) - 1 for i in selected if i.strip().isdigit()]

    # 💥 Clear or create fresh log file
    log_file = "latency_log.json"
    if os.path.exists(log_file):
        os.remove(log_file)
        print("🧹 Previous latency log found and wiped.")
    else:
        print("📂 No existing latency log found. Starting fresh.")

    print("")  # spacer

    for i in selected:
        try:
            vm = vms[i]
            vm_name = vm.name
            location = vm.location
            rg = vm.id.split("/")[4]

            nic_id = vm.network_profile.network_interfaces[0].id
            nic_name = nic_id.split("/")[-1]
            nic = network_client.network_interfaces.get(rg, nic_name)

            ip_ref = nic.ip_configurations[0].public_ip_address
            if not ip_ref:
                print(f"⚠️ {vm_name} has no public IP. Skipping.")
                continue

            ip_name = ip_ref.id.split("/")[-1]
            public_ip = network_client.public_ip_addresses.get(rg, ip_name)

            ip = public_ip.ip_address
            if not ip:
                print(f"⚠️ {vm_name} public IP not yet assigned. Skipping.")
                continue

            latency, port = measure_tcp_latency(ip)
            if latency:
                log_latency(vm_name, location, ip, port, latency)
            else:
                print(f"❌ {vm_name} @ {ip}: No open TCP ports (22 or 3389).")

        except Exception as e:
            print(f"❌ Error with VM {vms[i].name}: {e}")

if __name__ == "__main__":
    main()
