# Azure VM Multi-Region Deployment Benchmark 🔧📊

This project automates the deployment of virtual machines across multiple Azure regions, logs deployment durations, and visualizes the results with a bar chart — all inside a containerized environment with web-based Azure CLI authentication. 🐳✨

## 📦 Project Overview

- Deploys VMs across user-selected Azure regions
- Measures and logs deployment time for each region
- Generates a graph comparing deployment durations
- Runs in a Docker container with Azure CLI installed
- Exposes graph over a local web server (Flask)
- No volume binds required

> This was built as part of a mini-project for my Bachelor's in Computer Science (Cloud Specialization). The goal was to automate infrastructure deployment and benchmark performance — and it went beyond expectations by being fully containerized and web-served!

## 🚀 Technologies Used

- **Python 3.11**
- **Azure CLI**
- **Azure SDKs (azure-identity, azure-mgmt-*)**
- **Matplotlib**
- **Flask (for serving output)**
- **Docker**

## 🐳 Running the Project (Dockerized)

1. **Build the image:**

   ```bash
   docker build -t azure-benchmark .

2. Run the container:
docker run -it -p 5000:5000 azure-benchmark

3. Login to Azure CLI when prompted: The script uses az login, which will prompt you to authenticate via the browser.

4. View Results: After deployment completes, navigate to:  http://localhost:5000 Your Results should look like this

5. ![output](https://github.com/user-attachments/assets/e0a5e034-59dc-4c5b-8cfd-9d363b6bc49c)

6. Check the "versions" folder for earlier script versions and development observations. This reflects the iterative approach taken during development.


Future Plans:
> Add support for benchmarking other Azure resources (Storage, App Services, etc.). Seperate Repositories will be created. Once finished may be merged.

> Create an AWS counterpart for cross-cloud comparison

> Export graphs and logs as PDFs

> CI/CD Integration via GitHub Actions


Feel Free To Contact and Contribute!
