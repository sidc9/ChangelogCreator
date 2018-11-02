# CreateChangelog

As the name suggests, this script creates a Changelog file from git history.

The Changelog is organised as follows:

        ## version (date):
          CATEGORY:
              COMMIT MESSAGE

## Version

Git tags are used to determine the version. 

If tags are unavailable, as a fallback the commit message is searched for version info 
in the following format
    
    (vMAJOR.MINOR.PATCH)
    (vSomeVersionInfo)

As long as the version is within parentheses and starts with 'v', it will be picked up.

If that also does not work, then the git SHA hash can be used. By default,
commits without version info are grouped together under the version 'untagged'.
If the input argument '--no-group' is passed, then the hashes are used as 
versions.

## Categories
    
* ADDED
* REMOVED
* FIXED
* CHANGED
* DEPRECATED 
* IMPROVED

The script attempts to categorize a commit based on the commit message. If it
fails to categorize, it simply puts the commit under UNCATEGORIZED (for 
example, if a commit message contains the word "fixed" it gets categorized
as FIXED).


## Options

`--no-group`

Commits for which version could not be determined will *not* be grouped together,
instead their git hash will be used as the version.

`--detail`

The git hash of each commit can be included along with the message.

`--max`

The number of commits to use to create the Changelog can be controlled.

