
build:
	python3 -m build

install:
	cd dist && pip install --upgrade --force-reinstall pythontoolbox-0.0.1-py3-none-any.whl
