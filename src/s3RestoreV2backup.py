import argparse
import json
import boto3
from botocore.exceptions import ClientError
import os
from git import Repo
from pathlib import Path
from alive_progress import alive_bar
import subprocess

FILE_COUNT = 0

def check_object_exists(bucket_name, key):
    s3 = boto3.resource('s3')
    try:
        s3.Object(bucket_name, key).load()
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            # Something else has gone wrong.
            return False
    else:
        # The object does exist.
        return True


def sync_to_s3(local_folder, bucket_name, repo_name):
    s3 = boto3.client('s3')
    global FILE_COUNT
    FILE_COUNT = 0

    sync_command = f"aws s3 sync {local_folder}/ s3://{bucket_name}/{repo_name}/"
    subprocess.call(sync_command, shell=True)

    # for subdir, dirs, files in os.walk(local_folder):
    #     for file in files:
    #         FILE_COUNT += 1
    # with alive_bar(FILE_COUNT, title='Uploading files to S3') as bar:
    #     for subdir, dirs, files in os.walk(local_folder):
    #         for file in files:
    #             full_path = os.path.join(subdir, file)
    #             if check_object_exists(bucket_name, repo_name + "/" + full_path[len(local_folder)+1:]) is False:
    #                 with open(full_path, 'rb') as data:
    #                     s3.upload_fileobj(data, bucket_name, repo_name + "/" + full_path[len(local_folder)+1:])
    #             bar()

def distribute_in_s3(source_bucket, target_bucket, repo_name):
    s3 = boto3.resource('s3')
    src_bucket = s3.Bucket(source_bucket)
    global FILE_COUNT
    FILE_COUNT = 0
    
    # for key in src_bucket.objects.filter(Prefix=repo_name).all():
    #         FILE_COUNT += 1
    
    # with alive_bar(FILE_COUNT, title='Distributing files to S3 bucket ' + target_bucket) as bar:
    #     for s3object in src_bucket.objects.filter(Prefix=repo_name).all():
    #         copySource = {
    #             'Bucket': s3object.bucket_name,
    #             'Key': s3object.key
    #         }
    #         if check_object_exists(target_bucket, s3object.key) is False:
    #             s3.meta.client.copy(copySource, target_bucket, repo_name)
    #         bar()
    sync_command = f"aws s3 sync s3://{source_bucket}/{repo_name}/ s3://{target_bucket}/{repo_name}/"
    subprocess.call(sync_command, shell=True)


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
                    list_objects_in_bucket(bucket, repo_name)
                    break
                for bucket in config_dict['buckets']:
                    if bucket != source_bucket:
                        distribute_in_s3(source_bucket, bucket, repo_name)
                        print(f'*****Repository content distributed to {bucket} *****')
                        list_objects_in_bucket(bucket, repo_name)

    except ValueError as ve:
        print('Failed to process ')
        print('Cause: ' + str(ve))

    except ClientError as error:
        print('Error Message: {}'.format(error))


if __name__ == '__main__':
    main()
