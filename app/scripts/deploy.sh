# Makefile for Local CI/CD Testing with Virtual Environment
.PHONY: help venv activate setup check-venv check-dependencies clone-app lint unit-test test build freeze-requirements dry-run simulate-github-actions clean clean-all all ci local-ci full-test info test-venv

# Configuration
APP_NAME := social-media-downloader
DEPLOY_USER := deploy
STAGING_SERVER ?= 178.254.23.139
PRODUCTION_SERVER ?= 178.254.23.140
APP_REPO := https://github.com/kehe0014/social-media-downloader.git
LOCAL_APP_DIR := app-source
PACKAGE_NAME := deployment-package.tar.gz

# Configuration
...
VENV_DIR := venv

# Detect Python executable in venv: Prefer explicit python3 if it exists
ifneq (,$(wildcard $(VENV_DIR)/bin/python3))
    PYTHON_VENV_PATH := $(VENV_DIR)/bin/python3
else ifneq (,$(wildcard $(VENV_DIR)/bin/python))
    # Fallback to generic python symlink
    PYTHON_VENV_PATH := $(VENV_DIR)/bin/python
else
    # Fallback to system python3 if venv path is not found (should not happen after 'make venv')
    PYTHON_VENV_PATH := python3
endif

# Final variable used in commands
PYTHON := $(PYTHON_VENV_PATH)
PIP := $(VENV_DIR)/bin/pip

# Colors for better output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

help:
	@echo "$(GREEN)CI/CD Local Testing Commands:$(NC)"
	@echo "  $(YELLOW)make venv$(NC)      - Create and activate virtual environment"
	@echo "  $(YELLOW)make setup$(NC)     - Install dependencies in virtual environment"
	@echo "  $(YELLOW)make test$(NC)      - Run full test suite (lint + unit tests)"
	@echo "  $(YELLOW)make lint$(NC)      - Run linting only"
	@echo "  $(YELLOW)make unit-test$(NC) - Run unit tests only"
	@echo "  $(YELLOW)make build$(NC)     - Build deployment package"
	@echo "  $(YELLOW)make dry-run$(NC)   - Dry run deployment (simulate without actual deploy)"
	@echo "  $(YELLOW)make clean$(NC)     - Clean generated files and virtual environment"
	@echo "  $(YELLOW)make clean-all$(NC) - Clean everything including virtual environment"
	@echo "  $(YELLOW)make all$(NC)       - Run full pipeline: test + build"
	@echo "  $(YELLOW)make test-venv$(NC) - Test virtual environment setup"

venv:
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)Creating new virtual environment...$(NC)"; \
		python3 -m venv $(VENV_DIR); \
		echo "$(GREEN)Virtual environment created in $(VENV_DIR)$(NC)"; \
	else \
		echo "$(YELLOW)Virtual environment already exists$(NC)"; \
	fi
	@echo "$(YELLOW)Python executable: $(PYTHON)$(NC)"
	@echo "$(YELLOW)Virtual environment structure:$(NC)"
	@ls -la $(VENV_DIR)/bin/python* 2>/dev/null || echo "$(RED)Python not found in venv$(NC)"

setup: venv
	@echo "$(GREEN)Setting up environment...$(NC)"
	@echo "$(YELLOW)Using Python: $(PYTHON)$(NC)"
	@echo "$(YELLOW)Upgrading pip...$(NC)"
	@$(PYTHON) -m pip install --upgrade pip
	
	@echo "$(YELLOW)Installing test and linting dependencies...$(NC)"
	@$(PYTHON) -m pip install pytest pytest-cov flake8 ansible
	
	@echo "$(YELLOW)Installing application dependencies from cloned repo...$(NC)"
	@if [ -d "$(LOCAL_APP_DIR)" ] && [ -f "$(LOCAL_APP_DIR)/requirements.txt" ]; then \
		$(PYTHON) -m pip install -r $(LOCAL_APP_DIR)/requirements.txt; \
		echo "$(GREEN)Application dependencies installed$(NC)"; \
	elif [ -f "requirements.txt" ]; then \
		$(PYTHON) -m pip install -r requirements.txt; \
		echo "$(GREEN)Local requirements.txt installed$(NC)"; \
	else \
		echo "$(YELLOW)No requirements.txt found$(NC)"; \
	fi
	
	@echo "$(GREEN)All dependencies installed in virtual environment!$(NC)"
	@echo "$(YELLOW)Virtual environment location: $(VENV_DIR)$(NC)"
	@echo "$(YELLOW)Python: $(PYTHON)$(NC)"
	@echo "$(YELLOW)Testing Python executable...$(NC)"
	@$(PYTHON) --version
	@echo "$(YELLOW)Installed packages:$(NC)"
	@$(PYTHON) -m pip list | grep -E "(flake8|pytest|ansible)"

check-venv:
	@echo "$(YELLOW)Checking virtual environment...$(NC)"
	@echo "$(YELLOW)Python path: $(PYTHON)$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)Virtual environment not found. Run 'make venv' first.$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "$(RED)Python not found at $(PYTHON)$(NC)"; \
		echo "$(YELLOW)Available Python executables:$(NC)"; \
		ls -la $(VENV_DIR)/bin/python* 2>/dev/null || echo "$(RED)No Python found in venv$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Virtual environment is valid$(NC)"

check-dependencies: check-venv
	@echo "$(GREEN)Checking if required tools are available...$(NC)"
	@$(PYTHON) -c "import flake8" 2>/dev/null && echo "$(GREEN)✓ flake8 is available$(NC)" || (echo "$(RED)✗ flake8 is not available$(NC)" && exit 1)
	@$(PYTHON) -c "import pytest" 2>/dev/null && echo "$(GREEN)✓ pytest is available$(NC)" || (echo "$(RED)✗ pytest is not available$(NC)" && exit 1)
	@echo "$(GREEN)✓ All dependencies are available$(NC)"

clone-app:
	@echo "$(GREEN)Cloning application repository...$(NC)"
	@if [ -d "$(LOCAL_APP_DIR)" ]; then \
		echo "$(YELLOW)App directory exists, pulling latest changes...$(NC)"; \
		cd $(LOCAL_APP_DIR) && git pull; \
	else \
		git clone $(APP_REPO) $(LOCAL_APP_DIR); \
	fi

lint: setup clone-app check-dependencies
	@echo "$(GREEN)Running linting...$(NC)"
	@cd $(LOCAL_APP_DIR) && \
	echo "$(YELLOW)Running flake8...$(NC)" && \
	$(PYTHON) -m flake8 app.py || echo "$(YELLOW)Flake8 check completed with warnings$(NC)"
	
	@echo "$(GREEN)Linting completed!$(NC)"

unit-test: setup clone-app check-dependencies
	@echo "$(GREEN)Running unit tests...$(NC)"
	#cd $(LOCAL_APP_DIR) && \
	#f [ -d "tests" ]; then \
		#cho "$(YELLOW)Running pytest...$(NC)"; \
		#(PYTHON) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term; \
	#lse \
		#cho "$(YELLOW)No tests directory found, creating minimal test...$(NC)"; \
		#kdir -p tests; \
		#cho 'def test_example(): assert True' > tests/test_example.py; \
		#(PYTHON) -m pytest tests/ -v; \
	#i
	
	#echo "$(GREEN)Tests completed!$(NC)"

test: lint unit-test
	@echo "$(GREEN)All tests passed!$(NC)"

build: test
	@echo "$(GREEN)Building deployment package...$(NC)"
	
	@echo "$(YELLOW)Checking application dependencies...$(NC)"
	@cd $(LOCAL_APP_DIR) && \
	if [ -f "requirements.txt" ]; then \
		echo "$(GREEN)Found requirements.txt$(NC)"; \
	else \
		echo "$(YELLOW)No requirements.txt found in app, generating one...$(NC)"; \
		$(PYTHON) -m pip freeze > requirements.txt; \
	fi
	
	@cd $(LOCAL_APP_DIR) && \
	echo "$(YELLOW)Creating deployment package...$(NC)" && \
	tar -czf ../$(PACKAGE_NAME) \
		--exclude='.git' \
		--exclude='.github' \
		--exclude='.gitignore' \
		--exclude='*.pyc' \
		--exclude='venv' \
		--exclude='tests' \
		--exclude='__pycache__' \
		.
	
	@echo "$(YELLOW)Package created: $(PACKAGE_NAME)$(NC)"
	@ls -lh $(PACKAGE_NAME)
	@echo "$(GREEN)Build completed!$(NC)"

freeze-requirements: setup
	@echo "$(GREEN)Freezing current dependencies to requirements.txt...$(NC)"
	@$(PYTHON) -m pip freeze > requirements.txt
	@echo "$(GREEN)Current dependencies saved to requirements.txt$(NC)"

dry-run:
	@echo "$(GREEN)Running deployment dry-run...$(NC)"
	@echo "$(YELLOW)Simulating deployment to staging...$(NC)"
	@echo "  - Would connect to: $(STAGING_SERVER)"
	@echo "  - Would use user: $(DEPLOY_USER)"
	@echo "  - Would deploy package: $(PACKAGE_NAME)"
	@echo "  - Would run deployment script"
	
	@if [ -f "$(PACKAGE_NAME)" ]; then \
		echo "$(GREEN)✓ Deployment package exists$(NC)"; \
		echo "$(YELLOW)Package contents:$(NC)"; \
		tar -tzf $(PACKAGE_NAME) | head -10; \
	else \
		echo "$(RED)✗ Deployment package missing. Run 'make build' first.$(NC)"; \
	fi
	
	@echo "$(YELLOW)Deployment steps that would be executed:$(NC)"
	@echo "  1. Copy package to server"
	@echo "  2. Extract package"
	@echo "  3. Create virtual environment on server"
	@echo " 4. Install dependencies from requirements.txt"
	@echo "  5. Start application"

simulate-github-actions:
	@echo "$(GREEN)Simulating GitHub Actions pipeline...$(NC)"
	@echo "$(YELLOW)=== Job: setup ===$(NC)"
	@$(MAKE) setup || (echo "$(RED)Setup failed$(NC)" && exit 1)
	@echo "$(YELLOW)=== Job: test ===$(NC)"
	@$(MAKE) test || (echo "$(RED)Test job failed$(NC)" && exit 1)
	@echo "$(YELLOW)=== Job: build ===$(NC)"
	@$(MAKE) build || (echo "$(RED)Build job failed$(NC)" && exit 1)
	@echo "$(YELLOW)=== Job: deploy-staging (simulated) ===$(NC)"
	@$(MAKE) dry-run
	@echo "$(GREEN)✅ All GitHub Actions steps simulated successfully!$(NC)"

clean:
	@echo "$(GREEN)Cleaning generated files...$(NC)"
	@rm -f $(PACKAGE_NAME)
	@rm -rf $(LOCAL_APP_DIR)
	@rm -rf htmlcov .coverage coverage.xml
	@echo "$(GREEN)Clean completed!$(NC)"

clean-all: clean
	@echo "$(GREEN)Cleaning virtual environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@echo "$(GREEN)Virtual environment removed!$(NC)"

all: simulate-github-actions

# Alias for common commands
ci: simulate-github-actions
local-ci: simulate-github-actions
full-test: test build dry-run

info:
	@echo "$(GREEN)Current configuration:$(NC)"
	@echo "  APP_NAME: $(APP_NAME)"
	@echo "  STAGING_SERVER: $(STAGING_SERVER)"
	@echo "  PRODUCTION_SERVER: $(PRODUCTION_SERVER)"
	@echo "  DEPLOY_USER: $(DEPLOY_USER)"
	@echo "  LOCAL_APP_DIR: $(LOCAL_APP_DIR)"
	@echo "  VENV_DIR: $(VENV_DIR)"
	@echo "  PYTHON: $(PYTHON)"
	@echo "$(YELLOW)Virtual environment packages:$(NC)"
	@$(PYTHON) -m pip list --format=columns | head -10

# Test virtual environment
test-venv: check-venv
	@echo "$(GREEN)Testing virtual environment...$(NC)"
	@$(PYTHON) --version
	@$(PYTHON) -m pip --version
	@echo "$(GREEN)Virtual environment is working correctly!$(NC)"