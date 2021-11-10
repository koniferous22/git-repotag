test-build:
	docker build . -f Dockerfile.test --tag=git-repotag-test
test-run:
	docker run --rm git-repotag-test
test-cleanup:
	docker rmi git-repotag-test
test: test-build test-run test-cleanup

format:
	black git_repotag/*
