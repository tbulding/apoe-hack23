#!/usr/bin/env python
import boto3

def folder_exists(bucket:str, path:str) -> bool:
    s3 = boto3.client('s3')
    path = path.rstrip('/') 
    try:
        resp = s3.list_objects_v2(
            Bucket=bucket, 
            Prefix=path, 
            Delimiter='/',
            MaxKeys=1)
        return 'CommonPrefixes' in resp
    except:
        return False
    
def delete_folder(bucket:str, key:str) -> bool:
    s3 = boto3.client('s3')
    resp = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=key
    )
    files_in_folder = resp["Contents"]
    files_to_delete = []

    for f in files_in_folder:
        files_to_delete.append({"Key":f["Key"]})
        print(str(f["Key"]) + " will be deleted")
    resp = s3.delete_objects(
        Bucket=bucket,
        Delete={
            "Objects":files_to_delete
        }
    )
    return resp

repo_name = "connect-integration-acqueon"
#scan all the buckets for the repo, delete any occurance and log it
s3_client = boto3.client('s3')
buckets = s3_client.list_buckets()
for bucket in buckets['Buckets']:
    bucket_name = bucket['Name']
    folder = folder_exists(bucket_name, repo_name)
    if folder ==True:
        print ("repo found in bucket " + bucket_name)
        resp = delete_folder(
            bucket=bucket_name,
            key=repo_name
        )
        print (resp)
        break
    else:
        print ("repo NOT found in folder " + bucket_name)


#scan the quickstart folder for the repo and delete any occurance and log it.

#scan the regional accounts for the repo, delete any occurance and log it.
#NOTE: Need to setup cross account access from the main assets account in order to permform this task under a single profile