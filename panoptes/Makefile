.PHONY: build

build:
	# --no-cache
	@docker build -t innox/fastapi-ollama .

build-dev:
	@docker build \
	-t innox/fastapi-ollama-dev \
	-f Dockerfile-dev .

run-dev:
	@docker run \
	-p 3000:3000 \
	-v $(PWD)/src:/app \
	innox/fastapi-ollama-dev

run-debug:
	@docker run -it \
	-p 3000:3000 \
	-v $(PWD)/src:/app \
	innox/fastapi-ollama-dev /bin/bash

run:
	@docker run -p 3000:3000 \
	-v $(PWD)/.env:/app \
	innox/fastapi-ollama

