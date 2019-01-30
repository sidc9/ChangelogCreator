#!/usr/bin/python
'''
CreateChangelog.py

As the name suggests, this script creates a Changelog file from git history.

The Changelog is organised as follows:

        ## version (date):
          CATEGORY:
              COMMIT MESSAGE

The categories are ADDED, REMOVED, FIXED, CHANGED, DEPRECATED and IMPROVED.
The script attempts to categorize a commit based on the commit message. If it
fails to categorize, it simply puts the commit under UNCATEGORIZED (for 
example, if a commit message contains the word "fixed" it gets categorized
as FIXED).

Git tags are used to determine the version.

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

CACHE = "createchangelog.cache"

COMMIT_TYPES = [
    "added", "removed", "fixed", "changed", "updated", "improved"
]

repo = Repo(".")
args = None
tagmap = {}
current_tag = None

def get_tag(hexsha):
    """ 
    returns a tag associated with
    a commit and sets the current_tag
    to that tag (returns None if there is no tag)
    """
    global current_tag
    tag = tagmap.get(hexsha, None)
    if tag is not None:
        current_tag = tag
    return tag

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
        self.version = None
        self.date = None
        self.signature = commit.hexsha[0:8]
        self._setDate(commit)
        self.msg = commit.message.rstrip().lstrip()
        self._setType()
        self._setVersion(commit.hexsha)

    def _setVersion(self, hexsha):
        tag = get_tag(hexsha)
        if tag is None:
            tag = current_tag

        self.version = tag.name


    def _setDate(self, commit):
        d = time.gmtime(commit.committed_date)
        self.date = "{}/{}/{}".format(d.tm_year, d.tm_mon, d.tm_mday)

    def __str__(self):
        return "#{} {} {} ({}) [{}]".format(self.signature, self.version, self.msg, self.date, self.type.name)

    def _versionParseFallback(self, commitMsg):
        ver = re.search("(.*)\s(\(v.*\))", commitMsg)
        if ver:
            self.msg = ver.group(1)
            v = ver.group(2)
            v = v.rstrip().lstrip()
            self.version = v[2:-1]

    def _setType(self):
        msg = self.msg.lower()
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

def createChangeLog(filename, changeLogMessages):
    with open(filename, "w") as f_cl:
        for group in changeLogMessages:
            f_cl.write("\n##{} ({}):".format(group["version"], group["date"]))
            for commit_type in group["commits"]:
                f_cl.write("\n " + commit_type.name + ":\n")
                for commit in group["commits"][commit_type]:
                    f_cl.write("  * " + commit.msg)
                    if args.detailed:
                        f_cl.write(" ({})".format(commit.signature))
                    f_cl.write("\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, help="max commits to use (default: all commits)")
    parser.add_argument("--detailed", action="store_true", help="include commit hashes")
    parser.add_argument("--no-group", action="store_true", help="do not group commits which cannot be described by a tag")
    parser.add_argument("--verbose", "-v", action="store_true", help="print verbose output")
    parser.add_argument("--output", "-o", type=str, default="changelog.txt", help="output filename to which changelog will be written")
    args = parser.parse_args()

    current_branch = repo.active_branch
    if current_branch.name != 'master':
        print "warning: current branch is {}, not MASTER".format(current_branch.name)

    fcommits = []
    if args.max:
        fcommits = list(repo.iter_commits(current_branch.name, max_count=args.max))
    else:
        fcommits = list(repo.iter_commits(current_branch.name))

    """ store tag info """
    s = sorted(repo.tags, key=lambda t: t.commit.committed_date, reverse=True)
    for tag in s:
        tagmap[tag.commit.hexsha] = tag

    if get_tag(fcommits[0].hexsha) is None:
        print "error: latest commit needs to be tagged"
        sys.exit(1)

    changeLogMessages = []
    for commit in fcommits:
        changeLogMsg = ChangeLogMsg(commit)

        if args.verbose:
            print changeLogMsg

        last_elem = {}
        if len(changeLogMessages) != 0:
            last_elem = changeLogMessages[-1]

        # if changeLogMsg.version is None:
        #     if args.no_group:
        #         changeLogMsg.version = changeLogMsg.signature
        #     else:
        #         changeLogMsg.version = "untagged"
        if args.no_group:
            changeLogMsg.version = changeLogMsg.signature
        
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

    createChangeLog(args.output, changeLogMessages)
