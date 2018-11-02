#!/usr/bin/python
'''
CreateChangelog.py

As the name suggests, this script creates a Changelog file from git history.
It only works with Git as of now.

The Changelog is organised as follows:

        ## version (date):
          CATEGORY:
              COMMIT MESSAGE

The categories are ADDED, REMOVED, FIXED, CHANGED, DEPRECATED and IMPROVED.
The script attempts to categorize a commit based on the commit message. If it
fails to categorize, it simply puts the commit under UNCATEGORIZED.

Git tags are used to determine the version. If tags are unavailable, the
commit message is searched for version info in the following format
    
    vMAJOR.MINOR.PATCH

If that also does not work, then the git SHA hash can be used. By default,
commits without version info are grouped together under the version 'untagged'.
If the input argument '--no-group' is passed, then the hashes are used as 
versions.


The git hash of each commit can be included along with the message using the
option '--detail'.

The number of commits to use to create the Changelog can be controlled
using the option '--max'.

@author Siddhanta Chakrabarty
'''

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
    "added", "removed", "fixed", "changed", "updated", "improved"
]

repo = Repo(".")
args = None

class COMMIT_TYPE(Enum):
    UNCATEGORIZED     = 0
    ADDED      = 1
    REMOVED    = 2
    FIXED      = 3
    CHANGED    = 4
    DEPRECATED = 5
    IMPROVED   = 6

class ChangeLogMsg(object):
    def __init__(self, commit):
        self.type = None
        self.msg = None
        self.version = None
        self.date = None
        self.signature = commit.hexsha[0:8]
        commitMsg = commit.message.rstrip().lstrip()
        self._setType(commitMsg)
        self._setVersion(commit)
        self._setMsg(commitMsg)
        self._setDate(commit)

    def _setVersion(self, commit):
        try:
            self.version = repo.git.describe(commit.hexsha, abbrev=0)
        except Exception as err:
            self._versionParseFallback(commit.message)

    def _setDate(self, commit):
        d = time.gmtime(commit.committed_date)
        self.date = "{}/{}/{}".format(d.tm_year, d.tm_mon, d.tm_mday)

    def __str__(self):
        return "Type: {}, Version: {}, Date: {}, Msg: {}".format(self.type, self.version, self.date, self.msg) 

    def _setMsg(self, commitMsg):
        self.msg = commitMsg

    def _versionParseFallback(self, commitMsg):
        ver = re.search("(.*)\s(\(v.*\))", commitMsg)
        if ver:
            self.msg = ver.group(1)
            v = ver.group(2)
            v = v.rstrip().lstrip()
            self.version = v[2:-1]

    def _setType(self, msg):
        msg = msg.lower()
        if msg.find("add") == 0:
            self.type = COMMIT_TYPE.ADDED
        elif msg.find("remove") == 0 or msg.find("delete") == 0:
            self.type = COMMIT_TYPE.REMOVED
        elif msg.find("fix") == 0 or msg.find("bugfix") == 0:
            self.type = COMMIT_TYPE.FIXED
        elif msg.find("change") == 0 or msg.find("update") == 0:
            self.type = COMMIT_TYPE.CHANGED
        elif msg.find("deprecate") == 0:
            self.type = COMMIT_TYPE.DEPRECATED
        elif msg.find("improve") == 0:
            self.type = COMMIT_TYPE.IMPROVED
        else:
            self.type = COMMIT_TYPE.UNCATEGORIZED

def createChangeLog(changeLogMessages):
    with open("changelog.txt", "w") as f_cl:
        for group in changeLogMessages:
            f_cl.write("\n##{} ({}):".format(group["version"], group["date"]))
            for commit_type in group["commits"]:
                f_cl.write("\n " + commit_type.name + ":\n")
                for commit in group["commits"][commit_type]:
                    f_cl.write("  * " + commit.msg)
                    if args.detailed:
                        f_cl.write(" ({})".format(commit.signature))
                    f_cl.write("\n")

def validate(commit):
    c = ChangeLogMsg(commit)
    return c.version is not None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, help="max commits to use (default: all commits)")
    parser.add_argument("--detailed", action="store_true", help="include commit hashes")
    parser.add_argument("--no-group", action="store_true", help="do not group commits which cannot be described by a tag")
    args = parser.parse_args()

    heads = repo.heads
    master = heads.master

    fcommits = []
    if args.max:
        fcommits = list(repo.iter_commits('master', max_count=args.max))
    else:
        fcommits = list(repo.iter_commits('master'))

    if not validate(fcommits[0]):
        print "Error: Latest commit needs to have version number"
        sys.exit(1)

    changeLogMessages = []
    for commit in fcommits:
        changeLogMsg = ChangeLogMsg(commit)

        last_elem = {}
        if len(changeLogMessages) != 0:
            last_elem = changeLogMessages[-1]

        if changeLogMsg.version is None:
            if args.no_group:
                changeLogMsg.version = changeLogMsg.signature
            else:
                changeLogMsg.version = "untagged"
        
        ver = last_elem.get("version", "")
        if ver == changeLogMsg.version:
            # append commit and replace element in main list
            elem = last_elem
            commits = elem["commits"].get(changeLogMsg.type, [])
            commits.append(changeLogMsg)
            elem["commits"][changeLogMsg.type] = commits
            changeLogMessages[-1] = elem
        else:
            # append element to main list
            elem = {}
            elem["version"] = changeLogMsg.version
            elem["date"] = changeLogMsg.date
            elem["commits"] = {changeLogMsg.type: [changeLogMsg]}
            changeLogMessages.append(elem)

    if DEBUG:
        print changeLogMessages

    createChangeLog(changeLogMessages)
