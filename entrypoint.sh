#!/bin/bash

clear
echo "============================================="
echo " ☁️ Azure Multi-Region Deployment Interface ☁️"
echo "============================================="
echo "[*] Logging into Azure CLI..."
az login --use-device-code

while true; do
    echo ""
    echo "============= MENU ============="
    echo "1. Deploy VMs & Benchmark"
    echo "2. Delete Resource Groups"
    echo "3. View Deployment Graph (Port 5000)"
    echo "4. Measure VM Latency"
    echo "5. Plot Latency Graph"
    echo "6. View Latency Graph (Port 5001)"
    echo "7. Exit"
    echo "================================"
    read -p "Enter your choice [1-7]: " choice

    case "$choice" in
        1)
            echo "[*] Running DeployVM.py..."
            python3 DeployVM.py
            ;;
        2)
            echo "[*] Running DeleteVM.py..."
            python3 DeleteVM.py
            ;;
        3)
            echo "[*] Launching Deployment Graph Viewer (Flask on port 5000)..."
            python3 serve_deployment.py
            ;;
        4)
            echo "[*] Running Latency Measurement Script..."
            python3 MeasureLatency.py
            ;;
        5)
            echo "[*] Plotting Latency Graph..."
            python3 PlotLatency.py
            ;;
        6)
            echo "[*] Launching Latency Graph Viewer (Flask on port 5001)..."
            python3 serve_latency.py
            ;;
        7)
            echo "Peace out, Cloud Commander 🚀"
            exit 0
            ;;
        *)
            echo "Invalid choice. Try again, mortal."
            ;;
    esac
done
