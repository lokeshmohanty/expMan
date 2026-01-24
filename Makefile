# Makefile for ExpMan

VERSION := $(shell grep 'version =' pyproject.toml | cut -d '"' -f 2)

.PHONY: help build clean release

help:
	@echo "ExpMan Makefile"
	@echo "  build    - Build the package distribution (wheel and sdist)"
	@echo "  clean    - Remove build artifacts"
	@echo "  release  - Tag, build, and create a GitHub release (requires 'gh' CLI)"

clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +

build: clean
	uv build

release: build
	@if [ -z "$(VERSION)" ]; then echo "Error: Could not extract version from pyproject.toml"; exit 1; fi
	@echo "Preparing release for version v$(VERSION)..."
	
	# Check if tag exists
	@if git rev-parse "v$(VERSION)" >/dev/null 2>&1; then \
		echo "Warning: Tag v$(VERSION) already exists locally."; \
	else \
		echo "Creating git tag v$(VERSION)..."; \
		git tag v$(VERSION); \
	fi

	@echo "Pushing tag to origin..."
	git push origin v$(VERSION)

	@echo "Creating GitHub Release..."
	@if command -v gh >/dev/null; then \
		gh release create v$(VERSION) dist/* --generate-notes; \
	else \
		echo "----------------------------------------------------------------"; \
		echo "Error: 'gh' CLI not found."; \
		echo "1. Install GitHub CLI: https://cli.github.com/"; \
		echo "2. Run 'gh auth login'"; \
		echo "3. Run 'gh release create v$(VERSION) dist/* --generate-notes'"; \
		echo "----------------------------------------------------------------"; \
	fi

	@$(MAKE) publish

publish: build
	@if [ -z "$(PYPI_TOKEN)" ]; then \
		echo "Error: PYPI_TOKEN environment variable is not set."; \
		echo "Please export PYPI_TOKEN=pypi-xxxxxxxx"; \
		exit 1; \
	fi
	@echo "Uploading to PyPI..."
	uv run twine --with twine upload dist/* -u __token__ -p $(PYPI_TOKEN)
