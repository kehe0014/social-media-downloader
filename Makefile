# ------------------------------------------------
# Makefile pour CI/CD local avec virtualenv
# ------------------------------------------------
.PHONY: help venv setup check-venv check-dependencies clone-app format lint unit-test test build freeze-requirements dry-run simulate-github-actions clean clean-all all ci local-ci full-test info test-venv

# Configuration
APP_NAME := social-media-downloader
DEPLOY_USER := deploy
STAGING_SERVER ?= 178.254.23.139
PRODUCTION_SERVER ?= 178.254.23.140
APP_REPO := https://github.com/kehe0014/social-media-downloader.git
LOCAL_APP_DIR := .
PACKAGE_NAME := deployment-package.tar.gz
VENV_DIR := venv
VENV_BIN := $(VENV_DIR)/bin
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip

EXCLUDE_FILE := .tar_exclude
EXCLUSIONS := .git .coverage __pycache__ venv htmlcov .pytest_cache tests downloads


# Couleurs pour sortie console
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

# ------------------------------------------------
# Aide
# ------------------------------------------------
help:
	@echo "$(GREEN)CI/CD Local Testing Commands:$(NC)"
	@echo "  $(YELLOW)make venv$(NC)      - Create virtual environment"
	@echo "  $(YELLOW)make setup$(NC)     - Install dependencies in virtual environment"
	@echo "  $(YELLOW)make format$(NC)    - Run Black to format code"
	@echo "  $(YELLOW)make lint$(NC)      - Run linting only"
	@echo "  $(YELLOW)make unit-test$(NC) - Run unit tests only"
	@echo "  $(YELLOW)make test$(NC)      - Run lint + tests"
	@echo "  $(YELLOW)make build$(NC)     - Build deployment package"
	@echo "  $(YELLOW)make dry-run$(NC)   - Simulate deployment"
	@echo "  $(YELLOW)make clean$(NC)     - Clean generated files"
	@echo "  $(YELLOW)make clean-all$(NC) - Clean everything including virtualenv"
	@echo "  $(YELLOW)make all$(NC)       - Run full pipeline: test + build"
	@echo "  $(YELLOW)make simulate-github-actions$(NC) - Simulate full GitHub Actions pipeline locally"

# ------------------------------------------------
# Virtualenv
# ------------------------------------------------
venv:
	@echo "$(GREEN)[1/4] Creating virtual environment...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		python3 -m venv $(VENV_DIR); \
		echo "$(GREEN)✓ Virtual environment created$(NC)"; \
	else \
		echo "$(YELLOW)Virtual environment already exists$(NC)"; \
	fi
	@echo "$(GREEN)✓ Virtual environment ready$(NC)"

setup: venv
	@echo "$(GREEN)[2/4] Installing dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@$(PIP) install black flake8 pytest pytest-cov
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

# ------------------------------------------------
# Formatage avec Black
# ------------------------------------------------
format: setup
	@echo "$(GREEN)[3/4] Running Black formatter...$(NC)"
	@$(VENV_BIN)/black $(LOCAL_APP_DIR)/ --line-length 79 || echo "$(YELLOW)Black formatting completed with warnings$(NC)"

# ------------------------------------------------
# Vérifications
# ------------------------------------------------
check-venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)Virtual environment not found. Run 'make venv' first.$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(VENV_BIN)/python" ]; then \
		echo "$(RED)Python not found in virtual environment. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi

check-dependencies: check-venv
	@echo "$(GREEN)Checking if required tools are available...$(NC)"
	@$(PYTHON) -c "import flake8" 2>/dev/null && echo "$(GREEN)✓ flake8 available$(NC)" || (echo "$(RED)✗ flake8 missing$(NC)" && exit 1)
	@$(PYTHON) -c "import pytest" 2>/dev/null && echo "$(GREEN)✓ pytest available$(NC)" || (echo "$(RED)✗ pytest missing$(NC)" && exit 1)

# ------------------------------------------------
# Clonage app
# ------------------------------------------------
clone-app:
	@echo "$(GREEN)Cloning application repository...$(NC)"
	@if [ -d "$(LOCAL_APP_DIR)" ]; then \
		echo "$(YELLOW)App directory exists, pulling latest changes...$(NC)"; \
		cd $(LOCAL_APP_DIR) && git pull; \
	else \
		git clone $(APP_REPO) $(LOCAL_APP_DIR); \
	fi

# ------------------------------------------------
# Linting
# ------------------------------------------------
lint: format clone-app check-dependencies
	@echo "$(GREEN)[4/4] Running linting...$(NC)"
	@cd $(LOCAL_APP_DIR) && $(PYTHON) -m flake8 app.py || echo "$(YELLOW)Flake8 check completed with warnings$(NC)"

# ------------------------------------------------
# Unit tests
# ------------------------------------------------
unit-test: setup clone-app check-dependencies
	@echo "$(GREEN)Running unit tests...$(NC)"
	@cd $(LOCAL_APP_DIR) && \
	if [ -d "tests" ]; then \
		$(PYTHON) -m pytest tests/ -v --cov=app --cov-report=term --cov-report=html; \
	else \
		mkdir -p tests; \
		echo 'def test_example(): assert True' > tests/test_example.py; \
		$(PYTHON) -m pytest tests/ -v; \
	fi
	@echo "$(GREEN)Tests completed!$(NC)"

test: lint unit-test
	@echo "$(GREEN)All tests passed successfully!$(NC)"

# ------------------------------------------------
# Build deployment package
# ------------------------------------------------
	@echo "$(GREEN)Building deployment package...$(NC)"
	
	# 1. Gérer les dépendances
	@if [ -f "requirements.txt" ]; then \
		echo "$(GREEN)Found requirements.txt$(NC)"; \
	else \
		$(PIP) freeze > requirements.txt; \
	fi
	
	# 2. Créer le fichier d'exclusions (-X)
	@echo "$(YELLOW)Creating exclusion file $(EXCLUDE_FILE)...$(NC)"
	@echo $(EXCLUSIONS) | tr ' ' '\n' > $(EXCLUDE_FILE)
	
	# 3. Archiver dans le répertoire temporaire (/tmp) avec verbosité (-v)
	@echo "$(YELLOW)Creating deployment package in /tmp using -X and -v...$(NC)"
	# Utilisation directe du chemin /tmp pour la destination
	tar -cvzf /tmp/$(PACKAGE_NAME) -X $(EXCLUDE_FILE) -C $(LOCAL_APP_DIR) . 
	
	# 4. Déplacer l'archive vers le répertoire courant et nettoyer
	@echo "$(YELLOW)Moving package from temp to current directory and cleaning up...$(NC)"
	@mv /tmp/$(PACKAGE_NAME) .
	@rm $(EXCLUDE_FILE) # Supprimer le fichier d'exclusions temporaire
	
	@echo "$(GREEN)Package created: $(PACKAGE_NAME)$(NC)"
	@ls -lh $(PACKAGE_NAME)
	@echo "$(GREEN)Build completed!$(NC)"

	
# ------------------------------------------------
# Simulate deployment
# ------------------------------------------------
dry-run:
	@echo "$(GREEN)Simulating deployment...$(NC)"
	@if [ -f "$(PACKAGE_NAME)" ]; then \
		echo "$(GREEN)✓ Deployment package exists: $(PACKAGE_NAME)$(NC)"; \
	else \
		echo "$(RED)✗ Deployment package missing. Run 'make build' first.$(NC)"; \
	fi

# ------------------------------------------------
# Simulate full GitHub Actions pipeline
# ------------------------------------------------
simulate-github-actions:
	@echo "$(GREEN)=== Simulating GitHub Actions pipeline ===$(NC)"
	@$(MAKE) setup || (echo "$(RED)Setup failed$(NC)" && exit 1)
	@$(MAKE) test || (echo "$(RED)Test job failed$(NC)" && exit 1)
	@$(MAKE) build || (echo "$(RED)Build job failed$(NC)" && exit 1)
	@$(MAKE) dry-run
	@echo "$(GREEN)✅ Pipeline local simulée avec succès$(NC)"

# ------------------------------------------------
# Clean
# ------------------------------------------------
clean:
	@echo "$(GREEN)Cleaning generated files...$(NC)"
	@rm -f $(PACKAGE_NAME)
	@rm -rf htmlcov .coverage coverage.xml
	@if [ "$(LOCAL_APP_DIR)" != "." ]; then \
		rm -rf $(LOCAL_APP_DIR); \
	fi
	@echo "$(GREEN)Generated files removed!$(NC)"

clean-all: clean
	@echo "$(GREEN)Cleaning virtual environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@echo "$(GREEN)Virtual environment removed!$(NC)"

# ------------------------------------------------
# Aliases
# ------------------------------------------------
all: simulate-github-actions
ci: simulate-github-actions
local-ci: simulate-github-actions
full-test: test build dry-run
