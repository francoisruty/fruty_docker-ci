### General overview

We have:
- a docker registry
- a node service listening for Github webhooks, pulling up-to-date github repos each time, and creating build jobs in the celery queue
- celery-flower that exposes an API to submit jobs to the celery queue
- celery workers that execute those jobs, which basically cp the repo content, cd into it, and perform a docker build/tag/push



### Test

For the sake of this test, we will use this repository as a build target.

First of all, make sure this repository has been cloned a first time: (the CI system will pull, but not do initial git clones):
docker-compose up -d
cd git_data
git clone XXXX
git checkout master

Make a curl to the watcher endpoint to simulate a github webhook.

Go to localhost:5000 to see the celery task.

When it's finished, check that the registry now contains the image:

curl -X GET localhost:5500/v2/_catalog


### NOTES

For a private repo, you will need to change a few things to allow github authentication.

In watcher/Dockerfile, you will need to add those lines:

RUN {{whatever command to get your github key, which we'll name "gitwatcher" in following lines}}
RUN chmod 600 ./gitwatcher
RUN mkdir ~/.ssh && touch ~/.ssh/known_hosts && ssh-keyscan github.com >> ~/.ssh/known_hosts && touch ~/.ssh/config && echo "Host github.com" >> ~/.ssh/config && echo "  StrictHostKeyChecking no" >> ~/.ssh/config && echo "  IdentityFile /usr/app/gitwatcher" >> ~/.ssh/config

This will enable you to performs clones and pulles on private repositories from inside the git watcher docker container.
