import json
import matplotlib.pyplot as plt
import os

log_file = "latency_log.json"
output_image = "latency_graph.png"

if not os.path.exists(log_file):
    print(f"❌ '{log_file}' not found. Run the latency measurement script first.")
    exit()

with open(log_file) as f:
    data = json.load(f)

if not data:
    print("📭 No latency data to plot.")
    exit()

# Sort by latency
data.sort(key=lambda x: x['latency_ms'])

# Labels and values
labels = [f"{entry['location']}\n{entry['vm_name']}" for entry in data]
latencies = [entry['latency_ms'] for entry in data]

# Color code based on latency
def get_color(lat):
    if lat < 50:
        return 'green'
    elif lat < 100:
        return 'orange'
    else:
        return 'red'

colors = [get_color(lat) for lat in latencies]

# Plot
plt.figure(figsize=(12, 6))
bars = plt.bar(labels, latencies, color=colors)

for bar, latency in zip(bars, latencies):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        f"{latency:.1f} ms",
        ha='center',
        va='bottom',
        fontsize=8
    )

plt.title("TCP Latency to Azure VMs by Region", fontsize=14)
plt.xlabel("Region / VM")
plt.ylabel("Latency (ms)")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

plt.savefig(output_image)
print(f"📊 Latency graph saved as '{output_image}' ✅")
