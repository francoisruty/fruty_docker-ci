import os
import math
import shutil
import subprocess
import time

def ciBumpVersion(repo):
    filename = "/versions/" + repo + ".txt"
    if os.path.exists(filename):
        with open(filename, 'r') as myfile:
            data = myfile.read().replace('\n', '')
            version = int(float(data))
    else:
        version = 1
    version = version + 1
    with open(filename, 'w+') as myfile:
        myfile.write(str(version))
    return version


def logger(filename, string):
    # trigger str method only if string is int. If string is a string, it may fail when special chars are present
    # We cannot use .encode all the time since it does not work on ints
    if string is None:
        return ''
    if isinstance(string, (int, long)):
        string = str(string)
    if isinstance(string, basestring):
        print(" ")
    else:
        string = str(string)
    filename = "/logs/" + filename + ".txt"

    if os.path.exists(filename):
        append_write = 'a'  # append if already exists
    else:
        append_write = 'w'  # make a new file if not
    try:
        file = open(filename, append_write)
        file.write(string.encode('utf-8') + '\n')
        file.close()
    except:
        return 'ERROR LOGGING STUFF'
    return ''


def listFiles(path):
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return onlyfiles


# We make a wrapper to create a folder, since we are in the docker container.
# Some previous tasks may have created the folder already so we must clean things up
def createFolder(path):
    # I dunno why but sometimes we have files with folder names
    test = os.path.isfile(path)
    if test == True:
        os.remove(path)
    test = os.path.isdir(path)
    if test == True:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
    else:
        os.makedirs(path)


def launchShellCommand(taskId, command):
    try:
        res = subprocess.check_output(command,shell=True)
        res = res.decode('utf-8')
        logger(taskId, res)
        return res
    except subprocess.CalledProcessError as e:
        logger(taskId, e.output)
        # DO NOT call terminateWrapper here since itself calls launchShellCommand
        raise ValueError('Launch shell command FAILED')
