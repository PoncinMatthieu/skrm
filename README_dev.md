# How to contribute

## Run tests
- Run all test suites: `python -m unittest`
- Run a single test suite: `python -m unittest tests/test_main.py`

## build and push new version

- Update [skrm/version.py](skrm/version.py) file
- Create source dist of the package: `python setup.py sdist`
- Upload to pypi: `twine upload dist/skrm-<version>.tar.gz`
