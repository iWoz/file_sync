#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import ntpath
import os
import re
import platform

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
    SYNC_FILE_LIST = [line.strip().replace('\\','/') for line in f if os.path.isfile(line.strip().replace('\\','/'))]
except Exception as e:
    raise e
finally:
    f.close()

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        src_path = event.src_path.replace('\\','/')
        if src_path in SYNC_FILE_LIST:
            copy(src_path, DIR_FOR_GIT)
            os.chdir(DIR_FOR_GIT)
            git_add_cmd = "git add -A"
            git_commit_cmd = "git commit -m " + re.escape("Update "+os.path.basename(src_path))
            if platform.system() == "Windows":
                git_commit_cmd = "git commit -m Update."
            git_pull_cmd = "git pull origin master"
            git_push_cmd = "git push origin master"
            call(
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
