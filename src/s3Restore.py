import argparse
import json
import boto3
from botocore.exceptions import ClientError
import os
from git import Repo
from pathlib import Path

def sync_to_s3(local_folder, bucket_name, repo_name):
    s3 = boto3.client('s3')
    for subdir, dirs, files in os.walk(local_folder):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                s3.upload_fileobj(data, bucket_name, repo_name + "/" + full_path[len(local_folder)+1:])

def list_objects_in_bucket(bucket_name, repo_name):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name
                                  , Prefix=repo_name)
    for object in response['Contents']:
        print(object['Key'])

def main():

    parser = argparse.ArgumentParser(
        description='Restore a GitHub Repository to S3.')
    parser.add_argument(
        'repo_local_path', help='The local path of to clone the Repository to', type=str)
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
            Repo.clone_from(args.repo_url,repo_path)
        config_items = json.load(open(args.config_file))
        for item in config_items:
            if item['id'] == args.target_account:
                config_dict = item
                for bucket in config_dict['buckets']:
                    sync_to_s3(str(repo_path), bucket, repo_name)
                    print(f'*****Repository content uploaded to {bucket} *****')
                    list_objects_in_bucket(bucket, repo_name)

    except ValueError as ve:
        print('Failed to process ')
        print('Cause: ' + str(ve))

    except ClientError as error:
        print('Error Message: {}'.format(error))


if __name__ == '__main__':
    main()
