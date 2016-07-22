#!/usr/bin/python

import sys
import time
import ntpath
import os
import re

from subprocess import call
from shutil import copy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# git root path for files to push to remote
DIR_FOR_GIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# files to synchronize
SYNC_FILE_LIST = []
f = open(os.path.join(DIR_FOR_GIT, "file_list.txt"), "r")
try:
    SYNC_FILE_LIST = [line.strip() for line in f]
except Exception, e:
    raise e
finally:
    f.close()

# get filename without upper directory
def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path in SYNC_FILE_LIST:
            print event.src_path
            copy(event.src_path, DIR_FOR_GIT)
            cd_cmd = "cd "+DIR_FOR_GIT
            git_add_cmd = "git add -A"
            git_commit_cmd = "git commit -m " + re.escape("Update "+path_leaf(event.src_path))
            git_pull_cmd = "git pull origin master"
            git_push_cmd = "git push origin master"
            call(
                cd_cmd + "&&" +
                git_add_cmd + "&&" +
                git_commit_cmd + "&&" +
                git_pull_cmd + "&&" +
                git_push_cmd,
                shell=True
            )

if __name__ == "__main__":
    observer = Observer()
    event_handler = FileChangeHandler()

    for file_path in SYNC_FILE_LIST:
        copy(file_path, DIR_FOR_GIT)
        observer.schedule(event_handler, path=os.path.dirname(os.path.realpath(file_path)), recursive=False)

    observer.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
