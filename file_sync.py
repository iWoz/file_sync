#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import time

from shutil import copy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# git root path for files to push to remote
DIR_FOR_GIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# remote to push to, override with FILE_SYNC_REMOTE
GIT_REMOTE = os.environ.get("FILE_SYNC_REMOTE", "origin")


def current_branch(git_dir):
    """Return the checked out branch of git_dir, or "master" if unknown."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_dir, universal_newlines=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "master"
    return branch if branch and branch != "HEAD" else "master"


def load_sync_file_list(list_path):
    """Read absolute file paths, one per line, keeping only existing files."""
    with open(list_path, "r") as f:
        paths = [line.strip().replace('\\', '/') for line in f]
    return [path for path in paths if os.path.isfile(path)]


def git_commands(src_path, remote, branch):
    """Build the git commands to commit and push src_path as argument lists.

    Arguments are passed to git directly without a shell, so file names
    containing shell metacharacters cannot inject commands.
    """
    return [
        ["git", "add", "-A"],
        ["git", "commit", "-m", "Update " + os.path.basename(src_path)],
        ["git", "pull", remote, branch],
        ["git", "push", remote, branch],
    ]


def sync_file(src_path, git_dir, remote, branch):
    """Copy src_path into git_dir, then commit and push it.

    Stops at the first failing command, like chaining them with "&&".
    """
    copy(src_path, git_dir)
    for cmd in git_commands(src_path, remote, branch):
        if subprocess.call(cmd, cwd=git_dir) != 0:
            return False
    return True


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, sync_file_list, branch):
        super(FileChangeHandler, self).__init__()
        self.sync_file_list = sync_file_list
        self.branch = branch

    def on_modified(self, event):
        src_path = event.src_path.replace('\\', '/')
        if src_path in self.sync_file_list:
            sync_file(src_path, DIR_FOR_GIT, GIT_REMOTE, self.branch)


def main():
    sync_file_list = load_sync_file_list(os.path.join(DIR_FOR_GIT, "file_list.txt"))
    # branch to push to, override with FILE_SYNC_BRANCH
    branch = os.environ.get("FILE_SYNC_BRANCH") or current_branch(DIR_FOR_GIT)

    observer = Observer()
    event_handler = FileChangeHandler(sync_file_list, branch)

    for file_path in sync_file_list:
        copy(file_path, DIR_FOR_GIT)
        observer.schedule(event_handler, path=os.path.dirname(os.path.realpath(file_path)), recursive=False)

    observer.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
