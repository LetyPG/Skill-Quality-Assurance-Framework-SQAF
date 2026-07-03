# Skill: Containerized Environment Setup

## Metadata
- id: infra-env-setup-v1
- type: orchestration-devops
- severity: high
- engine: docker-compose

## Description
Validates the local orchestration layer by spinning up a standard multi-container stack (Application, Database, and Cache) and verifying service interconnectivity.

## Prerequisites
- Docker Engine >= 24.0.0 installed and running.
- Docker Compose V2 plugin enabled.
- Port 8080 and 5432 available on host.

## Infrastructure Matrix
| Service | Image | Internal Port | External Port |
| :--- | :--- | :--- | :--- |
| Gateway | nginx:alpine | 80 | 8080 |
| Database | postgres:15-alpine | 5432 | 5432 |
| Cache | redis:7-alpine | 6379 | Isolated |

## Execution Steps

### Step 001: Stack Deployment
- **Action:** Execute network initialization and container provisioning.
- **Command:** `docker compose -f ./poc-stack/docker-compose.yml up -d`
- **Verification:** Query daemon state via `docker compose ps` to ensure all 3 replicas show status `running`.

### Step 002: Health Check Propagation
- **Action:** Verify internal routing between Gateway and Database.
- **Command:** `curl -f http://localhost:8080/health`
- **Expected Outcome:** HTTP status code 200 payload returns JSON mapping: `{"status":"UP", "db":"connected"}`.

## Teardown
- Force removal of containers and networks via `docker compose down -v`.