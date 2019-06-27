### General overview

We have:
- a docker registry
- a node service listening for Github webhooks, pulling up-to-date github repos each time, and creating build jobs in the celery queue
- celery-flower that exposes an API to submit jobs to the celery queue
- celery workers that execute those jobs, which basically cp the repo content, cd into it, and perform a docker build/tag/push



### Test

NOTE: this was tested on ubuntu 16.04

For the sake of this test, we will use this repository as a build target.

***Make sure you're on a linux OS. This docker-based simple CI system uses "docker in docker" with volumes binding on /var/run/docker.sock and /var/run/docker.sock
A lot of commercial CI systems do the same, to be able to perform "docker build" commands inside docker containers.
Those volume mappings do not work on Windows and OsX since on those OSes docker daemon actually runs inside a hidden linux VM, with volume mappings bridging docker container inside with Windows/OsX host where docker binary is not present.

***Make sure the registry (which listens on 127.0.0.1:5500) is allowed as insecure registry (http instead of https). Normally local registries are allowed by default as insecure, you can check that with docker config.
If that's not the case, do this:
sudo bash -c 'echo "DOCKER_OPTS=\"--insecure-registry 127.0.0.1:5500\"" >> /etc/default/docker'
sudo bash -c 'echo "{\"insecure-registries\": [\"127.0.0.1:5500\"]}" >> /etc/docker/daemon.json'
sudo systemctl restart docker


First of all, make sure this repository has been cloned a first time: (the CI system will pull, but not do initial git clones):
docker-compose up -d
docker-compose exec git-watcher /bin/bash
cd /git_data
git clone https://github.com/francoisruty/fruty_docker-ci.git
exit

Make a curl to the watcher endpoint to simulate a github webhook.

curl -X POST \
  127.0.0.1:6000/hook \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/json' \
  -d '{
  "ref": "refs/heads/master",
  "repository": {"name": "fruty_docker-ci"},
  "head_commit": {"id": "test"}
}'

You should get in return {"status":"success","data":"","message":"hook successful"}
This means the git watcher node service received the hook message, performed a git pull, and created a build task in the celery queue.

NOTE: the build task looks for all Dockerfile* files in the repository root. Here we have a bogus Dockefile_test, for the sake of testing. This Dockerfile will be used by the build task.
By convention, any Dockerfile_* will yield a build with image name {{repository}}_{{Dockerfile _* suffix}}

Go to localhost:5000 (flower web interface) to see the celery task.
You can go to ./logs/{task id} to see the logs.

When the task is finished, it must appear as "successful" check that the registry now contains the image:

curl -X GET 127.0.0.1:5500/v2/_catalog

You must get:
{"repositories":["fruty_docker-ci_test"]}

This means the CI successfully received the webhook, built the docker container for this repo, and pushed it on the Docker registry!


### NOTES

** Docker registry address

One could wonder why the build celery task uses 127.0.0.1:5500 for the registry  (its external address) instead of communicating with it directly container to container.
We are using "docker in docker" with volume mappings, which means the build task, even though it runs inside a worker container, really interacts with the host docker daemon. So when we specify the docker registry address with the docker tag command, we must use an address visible from the host.

** Private repo

For a private repo, you will need to change a few things to allow github authentication.

In watcher/Dockerfile, you will need to add those lines:

RUN {{whatever command to get your github key, which we'll name "gitwatcher" in following lines}}
RUN chmod 600 ./gitwatcher
RUN mkdir ~/.ssh && touch ~/.ssh/known_hosts && ssh-keyscan github.com >> ~/.ssh/known_hosts && touch ~/.ssh/config && echo "Host github.com" >> ~/.ssh/config && echo "  StrictHostKeyChecking no" >> ~/.ssh/config && echo "  IdentityFile /usr/app/gitwatcher" >> ~/.ssh/config

This will enable you to performs clones and pulles on private repositories from inside the git watcher docker container.
