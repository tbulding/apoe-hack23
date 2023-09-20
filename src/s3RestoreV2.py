import argparse
import json
from git import Repo
from pathlib import Path
import subprocess

def sync_to_s3(local_folder, bucket_name, repo_name):
    sync_command = f"aws s3 sync {local_folder}/ s3://{bucket_name}/{repo_name}/"
    subprocess.call(sync_command, shell=True)

def distribute_in_s3(source_bucket, target_bucket, repo_name):
    sync_command = f"aws s3 sync s3://{source_bucket}/{repo_name}/ s3://{target_bucket}/{repo_name}/"
    subprocess.call(sync_command, shell=True)


def main():

    parser = argparse.ArgumentParser(
        description='Restore a GitHub Repository to S3.')
    parser.add_argument(
        'repo_local_path', help='The local path to clone the Repository to', type=str)
    parser.add_argument(
        'config_file', help='The path to the config file.', type=str)
    parser.add_argument(
        'target_account', help='The ID in the Config file of the target account.', type=str)
    parser.add_argument(
        'repo_url', help='The URL of the Repository to restore.', type=str)

    args = parser.parse_args()

    try:
        repo_name = (args.repo_url).split("/")[-1]
        repo_path = Path(args.repo_local_path + "/" + repo_name)
        if repo_path.exists() and repo_path.is_dir():
            ""
        else:
            Repo.clone_from(args.repo_url,repo_path,multi_options=['--recurse-submodules'])
        config_items = json.load(open(args.config_file))
        for item in config_items:
            if item['id'] == args.target_account:
                config_dict = item
                # Upload the repo to the first bucket then distribute to the other buckets
                source_bucket = ''
                for bucket in config_dict['buckets']:
                    source_bucket = bucket
                    sync_to_s3(str(repo_path), bucket, repo_name)
                    print(f'*****Repository content uploaded to {bucket} *****')
                    break
                for bucket in config_dict['buckets']:
                    if bucket != source_bucket:
                        distribute_in_s3(source_bucket, bucket, repo_name)
                        print(f'*****Repository content distributed to {bucket} *****')

    except ValueError as ve:
        print('Failed to process ')
        print('Cause: ' + str(ve))


if __name__ == '__main__':
    main()
