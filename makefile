# Source: https://hynek.me/articles/python-app-deps-2018/
# Remove the part for setuptools because we're not making it a package.
update-deps:
	pip install --upgrade pip-tools pip setuptools
	pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/prod.txt requirements/prod.in
	pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/dev.txt requirements/dev.in

init-dev:
	pip-sync requirements/prod.txt requirements/dev.txt
	rm -rf .tox

init-prod:
	pip-sync requirements/prod.txt
	rm -rf .tox

update-dev: update-deps init-dev

update-prod: update-deps init-prod

.PHONY: update-deps init-dev init-prod update-dev update-prod
