from __future__ import absolute_import
from celery.exceptions import SoftTimeLimitExceeded
from worker.celery import app
import time
import shutil
import os

from worker.utils import createFolder, launchShellCommand, logger, listFiles, ciBumpVersion


@app.task(name='build', soft_time_limit=7200, max_retries=1)
def build(repo, headCommit):
    taskId = build.request.id
    rootFolder = "/home/" + taskId

    repoFolder = rootFolder + "/" + repo
    logger(taskId,taskId)

    createFolder(rootFolder)

    shutil.copytree("/git_data/" + repo, repoFolder, symlinks=True)

    logger(taskId, "Bumping CI...")
    version = str(ciBumpVersion(repo))


    # NOTE: we detect all Dockerfiles
    dockerfiles = []
    files = listFiles(repoFolder)
    for file in files:
        if "Dockerfile" in file:
            dockerfiles.append(file)

    logger(taskId,"Dockerfiles: " + " ".join(dockerfiles))

    for dockerfile in dockerfiles:
        additionalTag = dockerfile.replace("Dockerfile","")
        dockerImgName = repo + additionalTag
        dockerImgName = dockerImgName.lower()

        logger(taskId, "Building docker image... : " + dockerImgName)
        res = launchShellCommand(taskId, 'cd ' + repoFolder + ' && docker build -f ' + dockerfile + ' -t ' + dockerImgName + ' .')
        logger(taskId, "Tagging docker image...")
        tag1 = os.environ["REGISTRY"] + "/" + dockerImgName + ":latest"
        res = launchShellCommand(taskId, 'docker tag ' + dockerImgName + ' ' + tag1)
        res = launchShellCommand(taskId, 'docker push ' + tag1)

        logger(taskId, "Tagging docker image for production... Version: " + version)
        tag2 = os.environ["REGISTRY"] + "/" + dockerImgName + ":" + version
        res = launchShellCommand(taskId, 'docker tag ' + dockerImgName + ' ' + tag2)
        res = launchShellCommand(taskId, 'docker push ' + tag2)
        tag3 = os.environ["REGISTRY"] + "/" + dockerImgName + ":" + headCommit
        res = launchShellCommand(taskId, 'docker tag ' + dockerImgName + ' ' + tag3)
        res = launchShellCommand(taskId, 'docker push ' + tag3)

    return "SUCCESS - version: " + version
