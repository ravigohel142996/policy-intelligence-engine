# Deployment Guide

This guide covers various deployment options for the Policy Intelligence Engine.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Production Considerations](#production-considerations)

---

## Local Development

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) Virtual environment tool (venv, conda)

### Setup

```bash
# Clone the repository
git clone https://github.com/ravigohel142996/policy-intelligence-engine.git
cd policy-intelligence-engine

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python tests/test_components.py

# Start the Streamlit application
streamlit run src/ui/app.py
```

The application will be available at `http://localhost:8501`

---

## Docker Deployment

### Build and Run with Docker

```bash
# Build the Docker image
docker build -t policy-intelligence-engine .

# Run the container
docker run -p 8501:8501 \
  -v $(pwd)/examples:/app/examples:ro \
  -v $(pwd)/outputs:/app/outputs \
  policy-intelligence-engine
```

### Using Docker Compose (Recommended)

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

Access the application at `http://localhost:8501`

### Docker Hub

Pull pre-built image (if available):

```bash
docker pull ravigohel142996/policy-intelligence-engine:latest
docker run -p 8501:8501 ravigohel142996/policy-intelligence-engine:latest
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: AWS ECS (Elastic Container Service)

1. **Build and push Docker image to ECR:**

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name policy-intelligence-engine

# Tag and push image
docker tag policy-intelligence-engine:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/policy-intelligence-engine:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/policy-intelligence-engine:latest
```

2. **Create ECS Task Definition:**

```json
{
  "family": "policy-intelligence-engine",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "policy-intelligence-engine",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/policy-intelligence-engine:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "memory": 2048,
      "cpu": 1024
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048"
}
```

3. **Create ECS Service with Load Balancer**

#### Option 2: AWS App Runner

```bash
# Deploy directly from GitHub
aws apprunner create-service \
  --service-name policy-intelligence-engine \
  --source-configuration '{
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/ravigohel142996/policy-intelligence-engine",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1024",
    "Memory": "2048"
  }'
```

#### Option 3: AWS EC2

```bash
# SSH into EC2 instance
ssh -i your-key.pem ec2-user@<ec2-ip>

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Pull and run
docker pull ravigohel142996/policy-intelligence-engine:latest
docker run -d -p 8501:8501 --restart always ravigohel142996/policy-intelligence-engine:latest
```

### Google Cloud Platform (GCP)

#### Cloud Run Deployment

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/<project-id>/policy-intelligence-engine

# Deploy to Cloud Run
gcloud run deploy policy-intelligence-engine \
  --image gcr.io/<project-id>/policy-intelligence-engine \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

#### GKE (Google Kubernetes Engine)

```bash
# Create cluster
gcloud container clusters create policy-intelligence-cluster \
  --num-nodes=2 \
  --machine-type=e2-standard-2

# Deploy
kubectl create deployment policy-intelligence-engine \
  --image=gcr.io/<project-id>/policy-intelligence-engine

kubectl expose deployment policy-intelligence-engine \
  --type=LoadBalancer \
  --port=80 \
  --target-port=8501
```

### Microsoft Azure

#### Azure Container Instances

```bash
# Create resource group
az group create --name policy-intelligence-rg --location eastus

# Deploy container
az container create \
  --resource-group policy-intelligence-rg \
  --name policy-intelligence-engine \
  --image ravigohel142996/policy-intelligence-engine:latest \
  --dns-name-label policy-intelligence \
  --ports 8501 \
  --memory 2 \
  --cpu 1
```

#### Azure App Service

```bash
# Create App Service plan
az appservice plan create \
  --name policy-intelligence-plan \
  --resource-group policy-intelligence-rg \
  --is-linux

# Create web app
az webapp create \
  --resource-group policy-intelligence-rg \
  --plan policy-intelligence-plan \
  --name policy-intelligence-engine \
  --deployment-container-image-name ravigohel142996/policy-intelligence-engine:latest
```

### Streamlit Cloud

1. Fork the repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repository and branch
6. Set main file path: `src/ui/app.py`
7. Click "Deploy"

---

## Production Considerations

### Security

1. **Authentication & Authorization:**
   - Implement user authentication (OAuth, SAML)
   - Add role-based access control (RBAC)
   - Use HTTPS/TLS for all connections

2. **Secrets Management:**
   - Use environment variables for sensitive data
   - Integrate with secret management services (AWS Secrets Manager, Azure Key Vault)
   - Never commit secrets to version control

3. **Network Security:**
   - Use VPC/VNet for network isolation
   - Configure security groups/firewall rules
   - Implement IP whitelisting if needed

### Performance

1. **Resource Allocation:**
   - Minimum: 2GB RAM, 1 vCPU
   - Recommended: 4GB RAM, 2 vCPU
   - For large-scale analysis: 8GB+ RAM, 4+ vCPU

2. **Optimization:**
   - Enable caching in Streamlit (`@st.cache_data`)
   - Use batch processing for large scenario sets
   - Consider distributed processing (Dask, Ray) for massive workloads

3. **Monitoring:**
   - Set up application monitoring (Datadog, New Relic)
   - Configure logging (CloudWatch, Stackdriver)
   - Implement health checks and alerts

### Scalability

1. **Horizontal Scaling:**
   - Use container orchestration (Kubernetes, ECS)
   - Implement load balancing
   - Consider stateless design for session management

2. **Data Management:**
   - Use persistent storage for outputs
   - Implement data backup and recovery
   - Consider database integration for result storage

3. **API Integration:**
   - Wrap core functionality in REST API (FastAPI)
   - Implement rate limiting
   - Add API documentation (OpenAPI/Swagger)

### Maintenance

1. **Updates:**
   - Implement CI/CD pipeline for automated deployments
   - Use blue-green or canary deployment strategies
   - Maintain rollback capability

2. **Backup:**
   - Regular backups of rule configurations
   - Version control for all rule sets
   - Document rule changes and rationale

3. **Monitoring:**
   - Track application performance metrics
   - Monitor resource utilization
   - Set up alerting for failures

### Compliance

1. **Data Privacy:**
   - Ensure compliance with GDPR, CCPA, HIPAA as applicable
   - Implement data anonymization for sensitive scenarios
   - Maintain audit logs

2. **Documentation:**
   - Document all deployed rule sets
   - Maintain change logs
   - Create incident response procedures

---

## Support

For deployment issues or questions:
- GitHub Issues: [Report a problem](https://github.com/ravigohel142996/policy-intelligence-engine/issues)
- Documentation: [README.md](../README.md)

---

## License

MIT License - See [LICENSE](../LICENSE) for details
