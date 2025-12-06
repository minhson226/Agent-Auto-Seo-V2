# Deployment Documentation

This directory contains documentation for deploying the Auto-SEO Platform to various environments.

## Available Guides

### Production Deployment

- **[Production Deployment Guide](production-deploy.md)** - Complete guide for deploying to production servers
  - Automated deployment via GitHub Actions
  - SSH-based deployment to production servers
  - Health checks and monitoring
  - Troubleshooting and rollback procedures

### Kubernetes Deployment

- **[Kubernetes Deployment Guide](kubernetes.md)** - Guide for deploying to Kubernetes clusters
  - Kubernetes manifests and configurations
  - Helm charts (if applicable)
  - Multi-environment setup

### Production Guide

- **[General Production Guide](production-guide.md)** - General production best practices
  - Security considerations
  - Performance optimization
  - Backup and disaster recovery

## Quick Start

For production deployment to the default server (194.233.71.21):

1. **Configure GitHub Secrets** (one-time setup):
   - `PROD_SSH_HOST` = `194.233.71.21`
   - `PROD_SSH_USER` = SSH username
   - `PROD_SSH_KEY` = Private SSH key

2. **Set up the production server** (one-time setup):
   ```bash
   ssh deploy@194.233.71.21
   mkdir -p /srv/apps/auto-seo
   cd /srv/apps/auto-seo
   # Replace with your repository URL if forked
   git clone https://github.com/minhson226/Agent-Auto-Seo-V2.git .
   cp .env.production.example .env
   # Edit .env with production values
   ```

3. **Deploy** (automatic):
   ```bash
   git push origin main
   ```

The GitHub Actions workflow will:
- Build Docker images
- Push to GHCR
- Deploy to production via SSH
- Run health checks
- Report status

## Architecture

```
┌─────────────────────────────────────────────────┐
│              GitHub Actions                      │
│  ┌─────────────┐  ┌──────────────┐             │
│  │ Build Images│→│ Push to GHCR  │             │
│  └─────────────┘  └──────────────┘             │
│         ↓                                        │
│  ┌─────────────────────────────────────┐        │
│  │    Deploy to Production (SSH)       │        │
│  │  - Pull code                         │        │
│  │  - Pull images from GHCR            │        │
│  │  - Run docker compose up -d         │        │
│  └─────────────────────────────────────┘        │
│         ↓                                        │
│  ┌─────────────────────────────────────┐        │
│  │      Health Checks (HTTP)           │        │
│  │  - Check /health endpoint           │        │
│  │  - Retry on failure                 │        │
│  └─────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         Production Server                        │
│         194.233.71.21:9101                      │
│                                                  │
│  /srv/apps/auto-seo/                            │
│  ├── docker-compose.prod.yml                    │
│  ├── .env (secrets)                             │
│  └── services/                                  │
│      ├── api-gateway (port 9101)               │
│      ├── auth-service                           │
│      ├── notification-service                   │
│      ├── content-generator                      │
│      └── analytics                              │
└─────────────────────────────────────────────────┘
```

## Service Ports

### External (Exposed)
- **9101** - API Gateway (production HTTP endpoint)

### Internal (Docker network only)
- 5432 - PostgreSQL
- 6379 - Redis
- 8123 - ClickHouse HTTP
- 9000 - ClickHouse Native / MinIO
- 5672 - RabbitMQ
- 15672 - RabbitMQ Management

## Environment Variables

Production environment variables are defined in `.env.production.example`. Copy this file to `.env` on the production server and update with actual values.

**Critical variables:**
- `POSTGRES_PASSWORD` - Database password
- `REDIS_PASSWORD` - Redis password
- `JWT_SECRET_KEY` - JWT signing key
- `ENCRYPTION_KEY` - Data encryption key
- `IMAGE_TAG` - Docker image tag (auto-set by deployment)

## Health Checks

All services expose health endpoints:
- API Gateway: `http://194.233.71.21:9101/health`
- Internal services: `http://localhost:<port>/health`

The deployment workflow automatically checks the API Gateway health endpoint after deployment.

## Support

For issues or questions:
1. Check the specific deployment guide
2. Review GitHub Actions logs
3. SSH into the server and check logs: `docker compose -f docker-compose.prod.yml logs`
4. Consult the troubleshooting section in the production deployment guide

## Security

- Never commit `.env` files
- Rotate secrets regularly
- Use strong passwords (16+ characters)
- Keep SSH keys secure
- Monitor access logs
- Enable firewall rules (only port 9101 should be public)
