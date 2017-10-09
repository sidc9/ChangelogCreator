# CreateChangelog

A simple script which can create a Changelog from Git commit history.

The commit message needs to have follow a specific format for this
script to parse it successfully.

## Commit Format

### Compulsory requirement
The latest commit must end in a version string. A sample version
string is given below:

(v0.10.5)

The opening and closing brackets are compulsory, as well as the
alphabet 'v'. The actual version string can be anything. So all
the following are VALID version strings.

* (v0)
* (v1.1.1.1)
* (vMyVersion42)

### Recommended (non-compulsory) requirement
Begin each commit with a short string describing the 'type'
of commit, followed by a colon. This helps the script in grouping
similar commits in the Changelog. For example, bugfixes can be
one group, while newly added features can be another.

The format of the commit type is,

*type*: *message*

Example:

* "added: feature X"
* "fixed: bug no. 22"
* "removed: old feature Y"
... and so on.

Recognized types:
* Add / Added
* Removed / Deleted
* Fixed / Bugfixed
* Changed
* Deprecated

It is case-insensitive. The tense also does not matter.
So "add" and "added" will be handled equally.

## Usage

Simple usage,

```
python CreateChangelog.py
```

Ignore cache,

```
python CreateChangelog.py --ignore-cache
```

Limit the number of commits to be used,

```
python CreateChangelog.py --max 3
```

## Cache Support

The script creates a cache which keeps track of the last commit used to create
a changelog. A new changelog will end just before that commit. This helps prevent
overlapping of Changelogs.

You can turn off the cache support by passing in the argument,

```
--ignore-cache
```

## Max commits

You can specify the max number of commits that the script should use to generate
changelog.

```
--max=50
```

## Future

Add support to enter date limit for commits to use in Changelog.
