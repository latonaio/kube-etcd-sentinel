docker-build:
	bash ./docker-build.sh

docker-push:
	bash ./docker-build.sh push

install:
	pipenv install --skip-lock
	pip install git+ssh://git@bitbucket.org/latonaio/python-base-images.git