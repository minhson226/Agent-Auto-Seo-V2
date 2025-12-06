# Production Deployment Guide

This document describes the automated production deployment process for the Auto-SEO Platform.

## Overview

The Auto-SEO Platform uses automated deployment via GitHub Actions to deploy to production servers using Docker Compose. The deployment is triggered automatically on pushes to the `main` branch after all tests pass.

## Deployment Architecture

### Server Configuration

- **Environment**: Production
- **Server IP**: `194.233.71.21`
- **Application Path**: `/srv/apps/auto-seo`
- **Public HTTP Port**: `9101`
- **Access URL**: `http://194.233.71.21:9101`

### Services Deployed

The production deployment includes:
- API Gateway (exposed on port 9101)
- Auth Service
- Notification Service
- Content Generator Service
- Analytics Service
- PostgreSQL Database
- Redis Cache
- ClickHouse Analytics Database
- MinIO Object Storage
- RabbitMQ Message Broker

## GitHub Secrets Configuration

The following secrets must be configured in the GitHub repository settings under `Settings > Secrets and variables > Actions`:

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `PROD_SSH_HOST` | Production server IP/hostname | `194.233.71.21` |
| `PROD_SSH_USER` | SSH username for deployment | `deploy` |
| `PROD_SSH_KEY` | Private SSH key for authentication | `-----BEGIN RSA PRIVATE KEY-----...` |

### Setting Up Secrets

1. Navigate to your repository on GitHub
2. Go to `Settings` > `Secrets and variables` > `Actions`
3. Click `New repository secret`
4. Add each secret with its corresponding value
5. Ensure the SSH key has proper permissions on the server

## Deployment Process

### Automatic Deployment (Recommended)

Deployments are automatically triggered when code is pushed to the `main` branch:

1. **Developer pushes to main**:
   ```bash
   git push origin main
   ```

2. **GitHub Actions pipeline executes**:
   - Lints and validates configuration files
   - Builds Docker images for all services
   - Pushes images to GitHub Container Registry (GHCR)
   - Tests infrastructure connectivity
   - Deploys to production (requires manual approval in GitHub)
   - Performs health checks

3. **Deployment steps on server**:
   - Navigates to `/srv/apps/auto-seo`
   - Pulls the latest code at the specific commit SHA
   - Sets the image tag environment variable
   - Pulls latest Docker images from GHCR
   - Restarts services with `docker compose up -d`
   - Waits for services to stabilize (30 seconds)

4. **Health check**:
   - Attempts to reach `http://194.233.71.21:9101/health`
   - Retries up to 10 times with 5-second delays
   - Verifies HTTP status code is 2xx or 3xx
   - Fails the deployment if health check doesn't pass

### Manual Deployment

If you need to deploy manually or troubleshoot:

```bash
# SSH into the production server
ssh deploy@194.233.71.21

# Navigate to the application directory
cd /srv/apps/auto-seo

# Pull the latest code
git pull origin main

# Set the image tag (use commit SHA or 'latest')
export IMAGE_TAG=latest

# Pull the latest images
docker compose -f docker-compose.prod.yml pull

# Restart the services
docker compose -f docker-compose.prod.yml up -d

# Check the status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f api-gateway
```

## Environment Configuration

### Production Environment Variables

The production server must have a `.env` file at `/srv/apps/auto-seo/.env` with the following variables:

```bash
# Database credentials
POSTGRES_USER=autoseo
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=autoseo

# Redis
REDIS_PASSWORD=<secure-password>

# RabbitMQ
RABBITMQ_USER=autoseo
RABBITMQ_PASSWORD=<secure-password>

# ClickHouse
CLICKHOUSE_USER=autoseo
CLICKHOUSE_PASSWORD=<secure-password>
CLICKHOUSE_DB=autoseo_analytics

# MinIO
MINIO_ROOT_USER=<minio-user>
MINIO_ROOT_PASSWORD=<secure-password>

# Application secrets
JWT_SECRET_KEY=<secure-jwt-secret>
ENCRYPTION_KEY=<32-byte-encryption-key>

# Optional: External services
OPENAI_API_KEY=<your-openai-key>
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=<smtp-user>
SMTP_PASSWORD=<smtp-password>
SLACK_WEBHOOK_URL=<slack-webhook>

# Image tag (automatically set by deployment script)
IMAGE_TAG=latest
```

**⚠️ Security Note**: Never commit the `.env` file to version control. Keep it secure on the production server.

## Health Checks

### API Gateway Health Endpoint

The API Gateway exposes a health check endpoint at `/health`:

```bash
curl http://194.233.71.21:9101/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "api-gateway"
}
```

### Service-Specific Health Checks

Each microservice has its own health endpoint:
- API Gateway: `http://localhost:8080/health`
- Auth Service: `http://localhost:8081/health`
- Notification Service: `http://localhost:8082/health`
- Content Generator: `http://localhost:8086/health`
- Analytics: `http://localhost:8087/health`

These are internal endpoints and not exposed externally. Use them for debugging on the server.

## Monitoring and Logs

### Viewing Logs

To view logs for a specific service:

```bash
# SSH into the server
ssh deploy@194.233.71.21
cd /srv/apps/auto-seo

# View logs for a specific service
docker compose -f docker-compose.prod.yml logs -f api-gateway
docker compose -f docker-compose.prod.yml logs -f auth-service
docker compose -f docker-compose.prod.yml logs -f postgres

# View logs for all services
docker compose -f docker-compose.prod.yml logs -f

# View last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 api-gateway
```

### Checking Service Status

```bash
# Check all running containers
docker compose -f docker-compose.prod.yml ps

# Check specific service health
docker inspect autoseo-api-gateway --format='{{.State.Health.Status}}'
```

### Container Resource Usage

```bash
# Check CPU and memory usage
docker stats --no-stream

# Check disk usage
docker system df
```

## Troubleshooting

### Deployment Fails

1. **Check GitHub Actions logs**:
   - Go to the repository on GitHub
   - Click on `Actions` tab
   - Select the failed workflow run
   - Review the logs for error messages

2. **Check if secrets are configured**:
   - Verify all required secrets are set in GitHub
   - Ensure the SSH key is correct and has proper permissions

3. **Verify server accessibility**:
   ```bash
   ssh deploy@194.233.71.21 "echo 'Connection successful'"
   ```

### Health Check Fails

1. **Check if services are running**:
   ```bash
   ssh deploy@194.233.71.21
   cd /srv/apps/auto-seo
   docker compose -f docker-compose.prod.yml ps
   ```

2. **Check API Gateway logs**:
   ```bash
   docker compose -f docker-compose.prod.yml logs --tail=100 api-gateway
   ```

3. **Test health endpoint manually**:
   ```bash
   curl -v http://194.233.71.21:9101/health
   ```

4. **Check if port 9101 is accessible**:
   ```bash
   # From your local machine
   telnet 194.233.71.21 9101
   
   # Or using curl
   curl -I http://194.233.71.21:9101/health
   ```

### Services Won't Start

1. **Check container logs**:
   ```bash
   docker compose -f docker-compose.prod.yml logs postgres
   docker compose -f docker-compose.prod.yml logs redis
   docker compose -f docker-compose.prod.yml logs api-gateway
   ```

2. **Check environment variables**:
   ```bash
   cat .env
   ```

3. **Verify Docker images are pulled**:
   ```bash
   docker images | grep autoseo
   ```

4. **Check for port conflicts**:
   ```bash
   sudo netstat -tlnp | grep 9101
   ```

5. **Restart all services**:
   ```bash
   docker compose -f docker-compose.prod.yml down
   docker compose -f docker-compose.prod.yml up -d
   ```

### Database Connection Issues

1. **Check PostgreSQL is running**:
   ```bash
   docker compose -f docker-compose.prod.yml exec postgres pg_isready -U autoseo
   ```

2. **Check database credentials**:
   ```bash
   docker compose -f docker-compose.prod.yml exec postgres psql -U autoseo -c "\l"
   ```

3. **Check database logs**:
   ```bash
   docker compose -f docker-compose.prod.yml logs postgres
   ```

### Out of Disk Space

1. **Check disk usage**:
   ```bash
   df -h
   docker system df
   ```

2. **Clean up old images and containers**:
   ```bash
   docker system prune -a --volumes
   ```

3. **Remove old logs**:
   ```bash
   docker compose -f docker-compose.prod.yml logs --tail=0 > /dev/null
   ```

## Rollback Procedure

If a deployment fails and you need to rollback:

1. **Find the previous working commit**:
   ```bash
   git log --oneline -10
   ```

2. **Deploy the previous version**:
   ```bash
   ssh deploy@194.233.71.21
   cd /srv/apps/auto-seo
   
   # Checkout the previous commit
   git checkout <previous-commit-sha>
   
   # Set the image tag
   export IMAGE_TAG=<previous-image-tag>
   
   # Restart services
   docker compose -f docker-compose.prod.yml pull
   docker compose -f docker-compose.prod.yml up -d
   ```

3. **Verify the rollback**:
   ```bash
   curl http://194.233.71.21:9101/health
   docker compose -f docker-compose.prod.yml ps
   ```

## Best Practices

1. **Always test changes locally** before pushing to main
2. **Monitor the deployment** through GitHub Actions
3. **Keep environment variables secure** and never commit them
4. **Regularly backup data** (PostgreSQL, ClickHouse, MinIO)
5. **Review logs** after each deployment to ensure everything is working
6. **Test health endpoints** after deployment
7. **Document any manual changes** made on the production server

## Security Considerations

1. **SSH Keys**: Ensure SSH keys are properly secured and rotated regularly
2. **Secrets Management**: Use GitHub Secrets for sensitive information
3. **Environment Variables**: Never commit `.env` files to version control
4. **Firewall**: Ensure only port 9101 is exposed to the internet
5. **HTTPS**: Consider adding a reverse proxy (nginx) with SSL/TLS in front of the application
6. **Database Access**: Database ports should not be exposed externally
7. **Regular Updates**: Keep Docker images and dependencies up to date

## Support and Escalation

If you encounter issues that cannot be resolved using this guide:

1. Check the GitHub Actions workflow logs
2. Review the application logs on the server
3. Consult the [Architecture Documentation](../architecture/overview.md)
4. Check the [API Documentation](../api/)
5. Contact the DevOps team or project maintainers

## Appendix

### Useful Commands

```bash
# Restart a specific service
docker compose -f docker-compose.prod.yml restart api-gateway

# Update a single service
docker compose -f docker-compose.prod.yml pull api-gateway
docker compose -f docker-compose.prod.yml up -d api-gateway

# Scale a service (if needed)
docker compose -f docker-compose.prod.yml up -d --scale content-generator=3

# Execute a command in a running container
docker compose -f docker-compose.prod.yml exec api-gateway /bin/sh

# Copy files from container
docker compose -f docker-compose.prod.yml cp api-gateway:/app/logs ./logs
```

### Environment Setup Script

For initial server setup, create this script at `/srv/apps/auto-seo/setup.sh`:

```bash
#!/bin/bash
set -e

echo "Setting up Auto-SEO production environment"

# Create necessary directories
mkdir -p /srv/apps/auto-seo
cd /srv/apps/auto-seo

# Clone repository (first time only)
# Note: Replace with your repository URL if you've forked this project
if [ ! -d ".git" ]; then
    git clone https://github.com/minhson226/Agent-Auto-Seo-V2.git .
fi

# Create .env file template
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with production values"
fi

echo "✅ Setup complete"
echo "Next steps:"
echo "1. Edit .env file with production credentials"
echo "2. Ensure GitHub Secrets are configured"
echo "3. Push to main branch to trigger deployment"
```

---

**Last Updated**: December 2025  
**Version**: 1.0.0
