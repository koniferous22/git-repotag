test-run:
	docker run git-repotag-test
test-build:
	docker build . -f Dockerfile.test --tag=git-repotag-test
