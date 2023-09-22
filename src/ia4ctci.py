#!/usr/bin/env python
import shutil
import argparse
from typing import OrderedDict
from git import Repo, GitError
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
from ruamel.yaml.main import round_trip_dump as yaml_dump
from ruamel.yaml.comments import CommentedMap as OrderedDict
import json
from pathlib import Path
from yaml.error import YAMLError
from taskcat._client_factory import Boto3Cache
from taskcat._template_params import ParamGen
import warnings
# warnings.simplefilter('ignore', yaml.error.UnsafeLoaderWarning)

parser = argparse.ArgumentParser()
parser.add_argument("repourl", nargs='?', help="Provide a the repository clone URL", type=str)
args = parser.parse_args()

ROOT_PATH = "ct/"
CT_FILES_DIR = "custom-control-tower-configuration"
MANIFEST_FILENAME = "manifest.yaml"
PARAMETERS_FILENAME = "parameters.json"

try:
    repo_name = (args.repourl).split("/")[-1][:-4]
    repo_path = Path("temp/" + repo_name)
    if repo_path.exists() and repo_path.is_dir():
        shutil.rmtree(repo_path)
    Repo.clone_from(args.repourl,"temp/" + repo_name)

except:
    raise Exception("Error Cloning the repository")

try:
    stream = open("temp/" + repo_name + "/.taskcat.yml", 'r')
    tc_file = yaml.load(stream)
    
except:
    raise Exception("Error loading .taskcat.yaml file")

try:
    # Container for each parameter object
    parameters = []
    param_dict = {}
    # capture any parameters declared at the project level
    for n in tc_file['project']:
        if 'parameters' in n:
            for p in tc_file['project']['parameters']:
                if isinstance(tc_file['project']['parameters'][p], str):
                    param_dict[p] = tc_file['project']['parameters'][p]
        # Get the value of the template attribute if available
        if 'template' in n:
            template = tc_file['project']['template']
        if 'name' in n:
            project_name = tc_file['project']['name']

    # Identify one test to work with
    for n in tc_file['tests']:
        # Get the name of the test being executed
        test_name = n
        # Get the value of the template attribute, if defined in project overwrite it
        if 'template' in tc_file['tests'][n]:
            template = tc_file['tests'][n]['template']
         # Get data for each parameter
        for x in tc_file['tests'][n]['parameters']:
            if isinstance(tc_file['tests'][n]['parameters'][x], str):
                param_dict[x] = tc_file['tests'][n]['parameters'][x]
        # Stop after getting details on a single test
        break

except:
    raise Exception("Error loading .taskcat.yaml file")

try:
    client = Boto3Cache();
    params = ParamGen(
    param_dict= param_dict,
    bucket_name= "aws-quickstart",
    region= "us-east-1",
    project_name= project_name,
    test_name= test_name,
    boto_client= client._boto3.client
)

except:
    raise Exception("Authentication Error")

try:
    ct_dir = "temp/" + repo_name + "/ct/"
    params_filepath = ct_dir + CT_FILES_DIR + "/" + PARAMETERS_FILENAME
    manifest_filepath = ct_dir + CT_FILES_DIR + "/" + MANIFEST_FILENAME
    
    # Create the CT folder, if it exits remove it and recreate it.
    dirpath = Path(ct_dir)
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(ct_dir)
        Path(ct_dir + CT_FILES_DIR).mkdir(parents=True, exist_ok=True)
    else:
        Path(ct_dir + CT_FILES_DIR).mkdir(parents=True, exist_ok=True)
    # Create the parameters file
    param_array = [{'parameter_key':i,'parameter_value':params.results[i]} for i in params.results]
    # with open(("temp/" + repo_name + "/ct/" + CT_FILES_DIR + "/" + PARAMETERS_FILENAME), "w") as outfile:
    #     json.dump(param_array, outfile, indent=4)
    # outfile.close()
    manifest_version = '2021-03-15'

    manifest_dict = OrderedDict({
        "region": params.region,
        "version": yaml.load(manifest_version),
        "resources":[OrderedDict({
            "name": project_name,
            "resource_file":"s3://aws-quickstart/" + project_name + "/" + template,
            "parameters":param_array,
            "deploy_method": "stack_set",
            "deployment_targets":OrderedDict({
                "organizational_units":['Workloads']
            }),
            "regions":[params.region]
        })]
    })

    with open(("temp/" + repo_name + "/ct/" + CT_FILES_DIR + "/" + MANIFEST_FILENAME), 'w') as outfile:
        yaml_dump(manifest_dict, outfile, indent=4, default_flow_style=False, explicit_start=True )
    outfile.close()

    shutil.make_archive(ct_dir + CT_FILES_DIR, 'zip', ct_dir + CT_FILES_DIR)

except YAMLError as exc:
    print(exc)
