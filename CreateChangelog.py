#!/usr/bin/python
import re
import sys
import os
import time
import argparse
from enum import Enum

import os.path as osp
from git import Repo

DEBUG = False
CACHE = "createchangelog.cache"

COMMIT_TYPES = [
    "added", "removed", "fixed", "changed", "updated"
]

class COMMIT_TYPE(Enum):
    OTHERS     = 0
    ADDED      = 1
    REMOVED    = 2
    FIXED      = 3
    CHANGED    = 4
    DEPRECATED = 5

class ChangeLogMsg(object):
    def __init__(self, commit):
        self.type = None
        self.msg = None
        self.version = None
        self.date = None
        self.parse_commit_msg(commit.message)
        self._setDate(commit)

    def _setDate(self, commit):
        d = time.gmtime(commit.committed_date)
        self.date = "{}/{}/{}".format(d.tm_year, d.tm_mon, d.tm_mday)

    def __str__(self):
        return "Type: {}, Version: {}, Date: {}, Msg: {}".format(self.type, self.version, self.date, self.msg) 

    def parse_commit_msg(self, msg):
        msg_split = msg.split(":")
        commitType = ""
        if len(msg_split)  > 1:
            commitType = msg_split[0]
            commitMsg  = msg_split[1]
        else:
            commitMsg = msg_split[0]
        self._setType(commitType)
        self._setMsg(commitMsg)

    def _setMsg(self, commitMsg):
        commitMsg = commitMsg.rstrip().lstrip()
        ver = re.search("(.*)\s(\(v.*\))", commitMsg)
        if ver:
            self.msg = ver.group(1)
            v = ver.group(2)
            v = v.rstrip().lstrip()
            self.version = v[2:-1]
        else:
            self.msg = commitMsg

    def _setType(self, commitType):
        commitType = commitType.lower()
        if commitType.find("add") == 0:
            self.type = COMMIT_TYPE.ADDED
        elif commitType.find("remove") == 0 or commitType.find("delete") == 0:
            self.type = COMMIT_TYPE.REMOVED
        elif commitType.find("fix") == 0 or commitType.find("bugfix") == 0:
            self.type = COMMIT_TYPE.FIXED
        elif commitType.find("change") == 0:
            self.type = COMMIT_TYPE.CHANGED
        elif commitType.find("deprecate") == 0:
            self.type = COMMIT_TYPE.DEPRECATED
        else:
            self.type = COMMIT_TYPE.OTHERS

def createChangeLog(changeLogMessages):
    with open("changelog.txt", "w") as f_cl:
        for ver, commitGroup in changeLogMessages:
            f_cl.write("\n## " + ver + ":\n")
            for commitType in commitGroup:
                if commitType != COMMIT_TYPE.OTHERS:
                    f_cl.write(" " + commitType.name + ":\n")
                for commitMsg in commitGroup[commitType]:
                    f_cl.write("  * " + commitMsg.msg + "\n")

def validate(commit):
    c = ChangeLogMsg(commit)
    return c.version is not None

def writeCache(commit):
    with open(CACHE, "w") as cache:
        cache.write(commit.hexsha)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--ignore-cache", action="store_false", help="create changelog with all"
                                                                     " commits specified by max-commits, ignoring the cache")
    parser.add_argument("--max", type=int, help="max commits to use to create the Changelog (default: all commits)")
    args = parser.parse_args()

    repo = Repo(".")
    heads = repo.heads
    master = heads.master

    fcommits = []
    if args.max:
        fcommits = list(repo.iter_commits('master', max_count=args.max))
    else:
        fcommits = list(repo.iter_commits('master'))
    changeLogMessages = []

    if not validate(fcommits[0]):
        print "Error: Latest commit needs to have version number"
        sys.exit(1)

    last_run_hexsha = ""
    if  args.ignore_cache and os.path.exists(CACHE):
        last_run_hexsha = open(CACHE, "r").read()

    current_ver = None
    for commit in fcommits:
        if last_run_hexsha == commit.hexsha:
            print "Changelog is already up to date. Nothing to do."
            break

        changeLogMsg = ChangeLogMsg(commit)

        if changeLogMsg.version:
            current_ver = changeLogMsg.version + " (" + changeLogMsg.date + ")"
            changeLogMessages.append((current_ver, {}))
        cl = changeLogMessages[-1][1]
        group = cl.get(changeLogMsg.type, [])
        group.append(changeLogMsg)
        changeLogMessages[-1][1][changeLogMsg.type] = group

    if DEBUG:
        print changeLogMessages

    createChangeLog(changeLogMessages)
    writeCache(fcommits[0])
