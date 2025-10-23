# ==============================================================================
# Makefile for Application Deployment
# Description: Build, test, and deploy application to various environments
# ==============================================================================

# ------------------------------------------------------------------------------
# Configuration & Variables
# ------------------------------------------------------------------------------
APP_NAME := social-media-dashboard
APP_PORT := 8501
DOCKER_REGISTRY := tdksoft341
K8S_NAMESPACE := my-app
DOCKER_COMPOSE_DEV := docker-compose.dev.yml
DOCKER_COMPOSE_PROD := docker-compose.prod.yml

# Docker Hub credentials (should be set as environment variables or in CI/CD)
DOCKER_USERNAME ?= tdksoft341
DOCKER_TOKEN ?= ${DOCKERHUB_TOKEN}

# Minikube configuration
MINIKUBE_PROFILE ?= minikube

# ------------------------------------------------------------------------------
# Primary Targets (shown in help)
# ------------------------------------------------------------------------------

##@ Primary

.PHONY: clean
clean: ## Clean up build artifacts and containers
	@echo "Cleaning up..."
	docker system prune -f
	docker volume prune -f
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__

.PHONY: build
build: ## Build Docker images
	@echo "Building Docker images..."
	docker build -t $(DOCKER_REGISTRY)/$(APP_NAME):latest .

.PHONY: up
up: ## Start development environment
	@echo "Starting development environment..."
	docker-compose -f $(DOCKER_COMPOSE_DEV) up -d

.PHONY: deploy-dev
deploy-dev: build push-minikube deploy-minikube ## Deploy to development (minikube)

.PHONY: deploy-staging
deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	# Add your staging deployment logic here

# ------------------------------------------------------------------------------
# Development & Testing
# ------------------------------------------------------------------------------

##@ Development

.PHONY: dev
dev: up ## Alias for starting development environment

.PHONY: down
down: ## Stop development environment
	docker-compose -f $(DOCKER_COMPOSE_DEV) down

.PHONY: logs
logs: ## View development logs
	docker-compose -f $(DOCKER_COMPOSE_DEV) logs -f


.PHONY: lint
lint: ## Run code linting
	@echo "Running linting..."
	# Add your linting commands here, e.g., flake8, black, etc.

# ------------------------------------------------------------------------------
# Minikube Deployment
# ------------------------------------------------------------------------------

##@ Kubernetes
.PHONY: simulate-deploy-k8s
simulate-deploy-k8s: ## Dry run the Kubernetes deployment steps locally
	@echo "========================================================"
	@echo "SIMULATING DEPLOYMENT DRY RUN to $(K8S_NAMESPACE) namespace"
	@echo "========================================================"
	
	@echo "1. Checking Namespace Creation (Simulated)"
	@echo "   (Action: kubectl create namespace $(K8S_NAMESPACE) --dry-run=client)"
	
	@echo "\n2. Simulating GHCR ImagePullSecret Creation (Dry Run)"
	@echo "   (Action: kubectl create secret docker-registry ghcr-auth-secret --namespace=$(K8S_NAMESPACE) --dry-run=client)"
	
	@echo "\n3. Checking Kubernetes Manifests (Dry Run - Full Output)"
	kubectl apply -f k8s/ --namespace=$(K8S_NAMESPACE) --dry-run=client -o yaml
	
	@echo "\n4. Simulating Deployment Rollout Status Check"
	@echo "   (Action: kubectl rollout status deployment/social-media-scrapper-deployment -n $(K8S_NAMESPACE) --dry-run=client)"
	
	@echo "\n5. Final Check: Would apply the following resources:"
	kubectl apply -f k8s/ -n $(K8S_NAMESPACE) --dry-run=client 
	
	@echo "\n✅ Dry run complete. Review the output for any Kubernetes errors."

.PHONY: minikube-setup
minikube-setup: ## Setup and configure minikube
	@echo "Setting up minikube..."
	minikube start --profile=$(MINIKUBE_PROFILE)
	minikube addons enable ingress --profile=$(MINIKUBE_PROFILE)
	@echo "Minikube dashboard: minikube dashboard --profile=$(MINIKUBE_PROFILE)"

.PHONY: minikube-tunnel
minikube-tunnel: ## Start tunnel for minikube services (run in separate terminal)
	@echo "Starting minikube tunnel (keep this running)..."
	minikube tunnel --profile=$(MINIKUBE_PROFILE)

.PHONY: eval-minikube
eval-minikube: ## Set docker env to minikube's
	@echo "Setting up minikube docker environment..."
	eval $$(minikube docker-env --profile=$(MINIKUBE_PROFILE))

.PHONY: build-minikube
build-minikube: eval-minikube ## Build image directly in minikube
	@echo "Building image in minikube environment..."
	docker build -t $(APP_NAME):latest .

.PHONY: push-minikube
push-minikube: ## Push image to registry (for minikube pull)
	@echo "Pushing image to Docker Hub..."
	docker push $(DOCKER_REGISTRY)/$(APP_NAME):latest

.PHONY: deploy-minikube
deploy-minikube: ## Deploy application to minikube
	@echo "Deploying to minikube..."
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/ingress.yaml
	@echo "Deployment complete. Use 'make minikube-status' to check status."

.PHONY: minikube-status
minikube-status: ## Check minikube deployment status
	@echo "=== Pods ==="
	kubectl get pods -n $(K8S_NAMESPACE)
	@echo "=== Services ==="
	kubectl get svc -n $(K8S_NAMESPACE)
	@echo "=== Ingress ==="
	kubectl get ingress -n $(K8S_NAMESPACE)

.PHONY: minikube-logs
minikube-logs: ## View application logs from minikube
	kubectl logs -l app=$(APP_NAME) -n $(K8S_NAMESPACE) -f

.PHONY: minikube-delete
minikube-delete: ## Delete application from minikube
	kubectl delete -f k8s/ -n $(K8S_NAMESPACE)

# ------------------------------------------------------------------------------
# Docker Management
# ------------------------------------------------------------------------------

##@ Docker

.PHONY: docker-login
docker-login: ## Login to Docker registry
	echo "$(DOCKERHUB_TOKEN)" | docker login -u "$(DOCKER_USERNAME)" --password-stdin

.PHONY: docker-push
docker-push: build ## Build and push to registry
	docker push $(DOCKER_REGISTRY)/$(APP_NAME):latest

.PHONY: docker-clean
docker-clean: ## Clean Docker images and containers
	docker system prune -a -f

# ------------------------------------------------------------------------------
# Utility Targets
# ------------------------------------------------------------------------------

##@ Utility

.PHONY: help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: status
status: ## Check status of all services
	@echo "=== Docker Containers ==="
	docker ps
	@echo "=== Kubernetes Pods ==="
	kubectl get pods -A

.PHONY: version
version: ## Show versions
	@echo "Docker: $$(docker --version)"
	@echo "Kubectl: $$(kubectl version --client --short)"
	@echo "Minikube: $$(minikube version --short)"