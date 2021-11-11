.PHONY: install
install:
	poetry install -E binary

tsab: install
	poetry run shiv .[binary] -o tsab -p /usr/bin/python3.8 -e timescale_ab.cli:main

container-software=$(shell which docker || which podman)
image-name=benchmark-image
container-name=benchmark-container

.PHONY: build-docker
build-docker:
	$(container-software) build -t $(image-name) .

.PHONY: docker-tsab
docker-tsab: build-docker
	$(container-software) run --rm -dit --name $(container-name) -e POSTGRES_PASSWORD=passowrd $(image-name)
	$(container-software) exec -it $(container-name) /bin/bash -c "while ! pg_isready -h localhost; do sleep 1; done"
	$(container-software) exec -it $(container-name) tsab existing /timescale_ab/query_params.csv

.PHONY: docker-shutdown
docker-shutdown:
	$(container-software) kill $(container-name)
