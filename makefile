# Source: https://hynek.me/articles/python-app-deps-2018/
# Remove the part for setuptools because we're not making it a package.

clone-pre-commit-hook:
	cp -i git_hooks/pre-commit .git/hooks/pre-commit

update-deps:
	pip install --upgrade pip-tools pip setuptools
	pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/prod.txt requirements/prod.in
	pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/dev.txt requirements/dev.in

sync-dev:
	pip-sync requirements/prod.txt requirements/dev.txt
	rm -rf .tox

sync-prod:
	pip-sync requirements/prod.txt
	rm -rf .tox

init-deps:
	pip install pip-tools setuptools

init-dev: init-deps sync-dev

init-prod: init-deps sync-prod

update-dev: update-deps sync-dev

update-prod: update-deps sync-prod

black-all:
	python -m black -t py38 "./blog_backend"

flake8-all:
	python -m flake8 --max-line-length 119 --config "./blog_backend/.flake8" "./blog_backend"

# mypy only works when in project root directory, so we need to switch working dir first.
mypy-all:
	pushd blog_backend && python -m mypy --config-file "./mypy.ini" "." || popd

.PHONY: clone-pre-commit-hook update-deps init-deps init-dev init-prod sync-dev sync-prod update-dev update-prod black-all flake8-all mypy-all
