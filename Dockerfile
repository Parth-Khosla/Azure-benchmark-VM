FROM python:3.11-slim

# Install Azure CLI dependencies
RUN apt-get update && apt-get install -y \
    curl ca-certificates apt-transport-https lsb-release gnupg bash iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Python packages
RUN pip install azure-identity azure-mgmt-resource azure-mgmt-compute \
    azure-mgmt-network azure-mgmt-subscription tabulate matplotlib flask

# Copy code into container
COPY . /app
COPY entrypoint.sh /app/entrypoint.sh
WORKDIR /app

# Set script permissions
RUN chmod +x /app/entrypoint.sh

# Expose Flask ports
EXPOSE 5000
EXPOSE 5001

# Default command
CMD ["/app/entrypoint.sh"]
