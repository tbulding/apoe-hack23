#!/usr/bin/env python

import argparse
import json
import os
from pathlib import Path
import git
from git import Repo
import re
from glob import glob
import subprocess
from git.exc import GitCommandError
import string
import random
from subprocess import CalledProcessError


def renameDocEdits(repo_path):
    # Rename the doc-edits branch to doc-edits-bu
    repo = git.Repo(repo_path)
    suffix = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=3))
    old_name = 'doc-edits'
    new_name = old_name + '-'  + suffix
    repo.git.branch('-m', old_name, new_name)
    try:
        repo.git.push('origin', '--set-upstream', new_name, '--no-verify')
        repo.git.push('origin', ':' + old_name, '--no-verify')
    except GitCommandError as gce:
        print(gce)
        return 'failed'
    return 'success'

def addBoilerplate(repo_path, boilerplate_path):
    # Add boilerplate to the repo
    repo = git.Repo(repo_path)
    repo.git.submodule('add', boilerplate_path, "docs/boilerplate")
    subprocess.run(
        "./docs/boilerplate/.utils/create_repo_structure.sh -d -c", cwd=repo_path)
    repo.git.commit(m='Adding skeleton for docs-as-code')
    try:
        repo.git.push('--set-upstream', 'origin', 'doc-edits')
    except GitCommandError as gce:
        if 'status 128' in str(gce.stdout):
            print('Failed to push, attempting with no verify')
            repo.git.push('--set-upstream', 'origin',
                          'doc-edits', '--no-verify')
    return 'success'

def getOrphan(repo_path, clone):
    repo = git.Repo(repo_path)
    repo.git.checkout('--orphan', 'doc-edits')
    repo.git.rm('-rf', '.')
    repo.git.clean('-f', '-d')
    return 'success'

def cloneRepo(repourl, repo_path):
    print (repourl)
    print (repo_path)
    repo = git.Repo.init(repo_path, bare=True)
    remote_branches = (repo.git.ls_remote(repourl)).split("\n")
    remote_branches = list(map(lambda b: re.search("([^\/]+$)", b), remote_branches))
    remote_branches = list(map(lambda b: b.group(1), remote_branches))
    if 'doc-edits' in remote_branches:
        # Need to rename the branch
        clone = 'doc-edits'
    elif 'gh-pages' in remote_branches:
        # Need to base doc-edits on gh-pages
        clone = 'gh-pages'
    elif 'main' in remote_branches:
        # Need to base doc-edits on main
        clone = 'main'
    else:
        # Need to base doc-edits on master
        clone = 'master'

    # Clone the Repository
    if repo_path.exists() and repo_path.is_dir():
       ''
       subprocess.call(['rm', '-rf', repo_path])
    # else:
    Repo.clone_from(
        url=repourl,
        to_path=repo_path,
        multi_options=['--branch ' + clone]
    )
    # Setup Git Defender
    try:
        subprocess.call(["/Users/tbulding/dev/tb/MySnippets/python/github/defender.py", repo_path._str])
    except CalledProcessError as cpe:
        print('Failed to setup Git Defender Error Message: {}'.format(cpe))
        return 'failed'

    return clone

def formaturl(url):
    if not re.match('(?:https)://', url):
        return 'https://{}'.format(url)
    return url

def main():

    parser = argparse.ArgumentParser(
        description='Restore a GitHub Repository to S3.')
    parser.add_argument(
        'config_file', help='The path to the config file.', type=str)
    parser.add_argument(
        'repo_url', help='The URL of the Repository to restore.', type=str)
    args = parser.parse_args()

    try:

        repourl = formaturl(args.repo_url)
        repo_name = (repourl).split("/")[-1]
        # Get the Config file
        config_items = json.load(open(args.config_file))
        repo_path = Path(config_items['clone_folder'] + "/" + repo_name)
        # Clone the Repository
        clone = cloneRepo(repourl, repo_path)
        # Copy the Partner Editable and Images files to a .temp folder
        paths = glob(repo_path._str + "/**/images", recursive=True)
        paths += glob(repo_path._str + "/**/partner_editable", recursive=True)
        for files in config_items['protected_files']:
            paths += glob(repo_path._str + "/" + files, recursive=False)
        temp_folder = Path(
            config_items['temp_folder'] + "/" + repo_name + "/.tmp")
        if not (temp_folder.exists() and temp_folder.is_dir()):
            subprocess.call(
                "mkdir -p " + config_items['temp_folder'] + "/" + repo_name + "/.tmp", shell=True)
        for path in paths:
            subprocess.call(
                "cp -r " + path + " " + config_items['temp_folder'] + "/" + repo_name + "/.tmp", shell=True)
        # if clone == 'doc-edits we need to rename it so we can create it from scratch
        if clone == 'doc-edits':
            renameDocEdits(repo_path._str)
        # Create a new orphan doc-edits branch
        orphan = getOrphan(repo_path._str, clone)
        # Make sure docs folder is removed
        docs = Path(repo_path / 'docs')
        modules = repo_path / '.git/modules'
        if os.path.isdir(docs) and docs.exists():
            subprocess.call("rm -rf " + docs._str, shell=True)
            subprocess.call("rm -rf " + modules._str, shell=True)

        print('ready for boilerplate')
        # Add New Boilerplate submodule
        orphan = addBoilerplate(
            repo_path._str, config_items['boilerplate_url'])
        # Copy the temp files to the repo
        subprocess.call("cp -r " + config_items['temp_folder'] +
                        "/" + repo_name + "/.tmp " + repo_path._str)
        print('tmp copied to repo')

    except ValueError as ve:
        print('Failed to process ')
        print('Cause: ' + str(ve))


if __name__ == '__main__':
    main()
