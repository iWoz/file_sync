# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import tempfile
import unittest

import file_sync


def git(cwd, *args):
    return subprocess.check_output(("git",) + args, cwd=cwd, universal_newlines=True).strip()


class FileSyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.remote = os.path.join(self.tmp, "remote.git")
        self.repo = os.path.join(self.tmp, "repo")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)

        git(self.tmp, "init", "--bare", "-b", "main", self.remote)
        git(self.tmp, "init", "-b", "main", self.repo)
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "remote", "add", "origin", self.remote)
        git(self.repo, "commit", "--allow-empty", "-m", "First commit.")
        git(self.repo, "push", "-u", "origin", "main")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, name, content):
        path = os.path.join(self.home, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_load_sync_file_list_skips_missing_files(self):
        existing = self.write(".zshrc", "export A=1\n")
        list_path = os.path.join(self.tmp, "file_list.txt")
        with open(list_path, "w") as f:
            f.write(existing + "\n" + os.path.join(self.home, "missing") + "\n\n")
        self.assertEqual(file_sync.load_sync_file_list(list_path), [existing])

    def test_current_branch(self):
        self.assertEqual(file_sync.current_branch(self.repo), "main")

    def test_current_branch_falls_back_outside_git(self):
        self.assertEqual(file_sync.current_branch(self.home), "master")

    def test_sync_file_commits_and_pushes(self):
        src = self.write(".zshrc", "export A=1\n")
        self.assertTrue(file_sync.sync_file(src, self.repo, "origin", "main"))
        self.assertEqual(git(self.remote, "log", "-1", "--format=%s", "main"), "Update .zshrc")
        self.assertEqual(git(self.remote, "show", "main:.zshrc"), "export A=1")

    def test_shell_metacharacters_in_file_name_are_not_executed(self):
        for name in ("a;whoami", "a`hostname`", "it's", "a>out"):
            src = self.write(name, "data\n")
            self.assertTrue(file_sync.sync_file(src, self.repo, "origin", "main"))
            self.assertEqual(git(self.remote, "log", "-1", "--format=%s", "main"), "Update " + name)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "out")))

    def test_sync_file_stops_when_nothing_to_commit(self):
        src = self.write(".zshrc", "export A=1\n")
        self.assertTrue(file_sync.sync_file(src, self.repo, "origin", "main"))
        self.assertFalse(file_sync.sync_file(src, self.repo, "origin", "main"))


if __name__ == "__main__":
    unittest.main()
