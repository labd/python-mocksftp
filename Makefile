.PHONY: test install


install:
	pip install -e .[test]

test:
	py.test

retest:
	py.test -vvs --lf

coverage:
	py.test --cov=mocksftp --cov-report=term-missing -p no:mocksftp

lint:
	ruff format --check src tests
	ruff check src tests


release:
	pip install twine wheel
	rm -rf dist/* build/*
	python setup.py sdist bdist_wheel
	twine upload -s dist/*
