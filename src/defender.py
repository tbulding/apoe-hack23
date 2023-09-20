#!/usr/bin/env python

import argparse
import os
from pathlib import Path
import sys
import git
from git import InvalidGitRepositoryError
import pexpect

def main():

    parser = argparse.ArgumentParser(
        description='Setup Git Defender')
    parser.add_argument(
        '-r', '--repo_path',
        dest='repo_path', 
        default=os.getcwd(),
        help='The local path to the root of the repository', 
        type=str)
    args = parser.parse_args()

 # Configure Git Defender
    try:
        repo_path = Path(args.repo_path)
        if os.path.isdir(repo_path) and repo_path.exists():
            cwd = repo_path._str
            repo = git.Repo(cwd)
        else:
            raise ValueError('Invalid Repository Path')
    except ValueError as ve:
        print('Failed to process ')
        print('Cause: ' + str(ve))
        raise
    except InvalidGitRepositoryError as igre:
        print('Invalid Repository Path')
        print('Cause: ' + str(igre))
        raise    
    
    email = repo.git.config('--get', 'user.email')
    exact_dict = {
        "confirm_setup_exact"     : "Should this be used for git defender?",
        "confirm_public_exact"    : "Please review your company's open source policy and type:",
        "confirm_email_exact"     : "Configure email allowed for commits",
        "config_email_exact"      : "Please enter the email you'd like to use for this repository",
        "confirm_email_exact"     : "confirm email:",
        "timeout"                 : pexpect.TIMEOUT,
        "end_of_file"             : pexpect.EOF
    }
    child = pexpect.spawn("git defender --setup " + cwd, encoding='utf-8')    
    child.logfile = sys.stdout
    
    while True:
        if child.isalive():
            i = child.expect_exact(list(exact_dict.values()), timeout=45)
            # i = child.expect_exact(exact_list, timeout=45)
            if i == 0 or i == 2: # Confirm Setup Prompt or Confirm Email Prompt
                child.sendline('y')
            elif i == 1: # Confirm Public Prompt
                response = child.buffer.replace("'","").replace("\r\n> ","").lstrip()
                child.sendline(s=response)
            elif i == 3 or i == 4: # Config Email Prompt or Confirm Email Prompt
                child.sendline(email)
            elif i == 5: # A timeout occured
                break
            elif i == 6: # EOF
                child.wait()
                break
        else:
            break



if __name__ == '__main__':
    main()
