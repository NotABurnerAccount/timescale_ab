.PHONY: install
install:
	poetry install

tsab: install
	poetry run shiv . -o tsab -p /usr/bin/python3.8 -e timescale_ab.cli:main
