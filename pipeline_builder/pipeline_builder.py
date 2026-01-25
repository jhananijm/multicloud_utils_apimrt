from jinja2 import Environment, FileSystemLoader
import json
import yaml
import subprocess
import os
import sys
import shutil
from collections import OrderedDict
from utils.display import Display
import maskpass
import argparse
import urllib.request
import configparser
import yaml
import random
from utils.fetch_timings import Timer

def get_deployment_list():
    with open("./../../../../../../config/deployments.yml", "r") as file:
        data=yaml.safe_load(file.read())
    return [i['instance'] for i in data['deployments']]

def fetch_lifecycle_list(deployment_name):
    with open(f"./../../../{deployment_name}/component.yml", "r") as file:
        data=yaml.safe_load(file.read())
    return [k for k, v in data['lifecycles'].items()]

def iac_set_config(deployment_name, key_path, value):
    print(f"Setting config for deployment {deployment_name} for key: {key_path}")
    command=f"iac edit-config -i {deployment_name} -p {key_path} -v {value}".split()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Unable to set the config details for Deployment: {deployment_name} Path: {key_path}")
        sys.exit(1)

def get_landscape_name():
    print("Fetching Landscape Name ...")
    command="iac get-config -d landscape-config -p config.landscapename".split()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Unable to fetch landscape name {result.stderr}")
        sys.exit(1)
    print(result.stdout.decode('utf-8').rstrip('\n'))
    return result.stdout.decode('utf-8').rstrip('\n')

def iac_get_config(deployment_name, key_path):
    command=f"iac get-config -i {deployment_name} -p {key_path}".split()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
         return result.stdout.decode().strip()
    print(f"Unable to fetch the config details for Deployment: {deployment_name} Path: {key_path}")
    value=input(f"Provide the value for : {key_path} to be set in the landscape : ")
    iac_set_config(deployment_name, key_path, value)
    return value

def check_developer_timer_mode(config_details, deployment_steps, full_deployment_list):
    non_deployment_list=['apim-rt', 'landscape-config']
    config_details["set_timer"] = "no"
    deployment_list=list(set(full_deployment_list) - set(non_deployment_list))
    display=Display()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev")
    parser.add_argument("--timer", default="no")
    parser.add_argument("--timeout", default="6h")
    args = parser.parse_args()
    if args.dev == "yes":
        print("\nEntering developer mode\n")
        print(f"Config Details: {config_details}\n")
        status=input("Do you want to edit the config file (Y/N): ")
        if status in ["Y", "y"]:         
            for key,item in config_details.items():
                data=input(f"Enter the new value for {key} (Old value: {item}):  ")
                if data != "":
                    config_details[key]=data
        display.print_table("Developer Deployment List", deployment_list)
        inp=input(f"\nCurrent Deployment order : {deployment_steps}\n\nEnter the new Deployment order (seperated by comma):  ")
        if inp != "":
            deployment_steps = inp.split(",")
            print(inp)
    if args.timer == "yes":
        config_details["set_timer"] = "yes"
        config_details["timimg_interval"] = "start: 9:00 AM \n stop: 09:00 AM"
    config_details["concourse_timeout"] = args.timeout
    return config_details, deployment_steps
    

def get_pipeline_configs(deployment_selected, team_name):
    landscape_name = get_landscape_name()
    config_details = {'tag_name': "v586"}
    config_details['lscrypt_password']= maskpass.askpass(prompt="Enter lscrypt Master Password: ", mask="*")
    os.environ["LANDSCAPE_MASTER_PASSWORD"] = config_details['lscrypt_password']
    result = subprocess.run(['lscrypt', 'unseal'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"lscrypt unseal failed\n {result.stderr.decode()}")
        sys.exit(1)
    config_details['landscape_name'] = landscape_name
    config_details['git_repo']=iac_get_config("repositories","repositories.git.landscape.repository")
    config_details['git_username']=iac_get_config("repositories","repositories.git.landscape.username")
    config_details['git_password']=iac_get_config("repositories","repositories.git.landscape.password")
    config_details['git_email']=iac_get_config("repositories","repositories.git.landscape.email")
    config_details['deployment_selected']=deployment_selected
    config_details['branch_name']=get_branch_name(config_details)
    config_details['lscrypt_password']=f"((vault:credentials.{landscape_name}_lscrypt_password))"
    config_details['concourse_team_name'] = team_name
    return config_details

def fetch_deployment_steps(deployment_selected):
    with open("./config/pipeline_flow.json", "r") as file:
        data=json.loads(file.read())
    if "," in data[deployment_selected]:
        return data[deployment_selected].split(",")
    else:
        return data[deployment_selected].split()


def check_deployment_activation(deployment_steps, full_deployment_list):
    for deployment in deployment_steps:
        if deployment not in full_deployment_list:
            print(f"Deployment {deployment} is not activated. Initialize the deployment first")
            sys.exit(1)


def generate_jobs(full_deployment_list, deployment_selected, config_details):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('jobs.yml')
    deployment_steps=fetch_deployment_steps(deployment_selected)
    check_deployment_activation(deployment_steps, full_deployment_list)
    jobs=[]
    deployment_check = {}
    config_details['previous_lifecycle_name']=""
    #landscape_name = get_landscape_name()
    config_details, deployment_steps = check_developer_timer_mode(config_details, deployment_steps, full_deployment_list)
    deployment_metadata=OrderedDict()
    for deployment in deployment_steps:
        lifecycle_metadata=[]
        for lifecycle in fetch_lifecycle_list(deployment):
            lifecycle_metadata.append(lifecycle)
            config_details['deployment_name']=deployment
            if f"{deployment}-{lifecycle}" in deployment_check.keys():
                deployment_check[f"{deployment}-{lifecycle}"] = deployment_check[f"{deployment}-{lifecycle}"] + 1
                #config_details['lifecycle_name'] = f"{lifecycle}-{deployment_check[f'{deployment}-{lifecycle}']}"
                config_details['job_count'] = f"-{deployment_check[f'{deployment}-{lifecycle}']}"
            else:
                deployment_check[f"{deployment}-{lifecycle}"] = 1
            config_details['lifecycle_name']= lifecycle
            config_details['concourse_notify_name'] = f"{deployment}_{lifecycle}"
            config_details['concourse_pipeline_name'] = f"{config_details['landscape_name']}-{deployment_selected}"
            #config_details['landscape_name'] = landscape_name
            if config_details["set_timer"] == "yes":
                config_details["set_timer_plan"] = f"- get: timer \n  passed: {config_details['previous_lifecycle_name']} \n  trigger: true"
            # Render the template
            output = template.render(config_details)
            job_data=yaml.safe_load(output)
            jobs.append(job_data)
            config_details['previous_lifecycle_name']=f"[{deployment}-{lifecycle}]"
            if deployment_check[f"{deployment}-{lifecycle}"] >= 2:
                config_details['previous_lifecycle_name']=f"[{deployment}-{lifecycle}-{deployment_check[f'{deployment}-{lifecycle}']}]"
        
        if deployment in deployment_metadata:
            deployment_metadata[f"{deployment}{config_details['job_count']}"]=lifecycle_metadata
        else:
            deployment_metadata[deployment]=lifecycle_metadata
    #Removing passed stage from first job
    del jobs[0]['plan'][0]['passed']
    with open("pipeline.yml", 'w') as file:
        file.write(f"jobs:\n{yaml.safe_dump(jobs)}")
    return deployment_metadata, config_details

def get_branch_name(config_details):
    git_link = config_details['git_repo'].replace("https://",f"https://{config_details['git_username']}:{config_details['git_password']}@")
    command=f"git ls-remote --heads {git_link}".split()

    try:
        result = subprocess.check_output(command)
        data=result.decode('utf-8')
        if ("main" not in data) ^ ("master" not in data):
            if "main" in data:
                return "main"
            elif "master" in data:
                return "master"
        else:
            print("Both (master or main) branch are present or both are absent")
            return input(f"\nProvide the branch name for {config_details['git_repo']}: ")
    except Exception as e:
        print(f"Unable to fetch any branch name from the repo {config_details['git_repo']} Error: {e}")
        return input(f"\nProvide the branch name for {config_details['git_repo']}: ")

def generate_resources_var_sources(config_details):
    env = Environment(loader=FileSystemLoader('templates'))
    if config_details["set_timer"] == "yes":
        tm = Timer()
        trigger_time, trigger_days = tm.get_timings()
        print(f"Timer will be set for Time: {trigger_time} and Days: {trigger_days}")
        config_details["timer_resource"] = f"- name: timer \n  type: time \n  source: \n   {trigger_time} \n   {trigger_days}"
    template = env.get_template("resources.yml")
    output = template.render(config_details)
    with open("templates/var_sources.yml", "r") as f:
        data=f.read()
    with open("pipeline.yml", 'a') as file:
        file.write(f"{output}\n{data}")


def generate_pipeline(deployment_selected, full_deployment_list, team_name):
    config_details = get_pipeline_configs(deployment_selected, team_name)
    deployment_stages, config_details = generate_jobs(full_deployment_list, deployment_selected, config_details)
    generate_resources_var_sources(config_details)
    return deployment_stages

def set_deployment(deployment_selected):
    with open("./config/deployment_selected", 'w') as file:
        file.write(deployment_selected)

def get_team_name():
    flag = True
    while flag:
        concourse_team_name = input("\nTeam List:\ndts-apimops\ndts-apimdev\n\nSelect the Team name:  ")
        if concourse_team_name not in ['dts-apimops', 'dts-apimdev']:
            print("Enter a valid Team Name")
        else:
            flag = False
    return concourse_team_name

def deploy_pipeline(team_name):
    #For deploying the pipeline using fly
    config = configparser.ConfigParser()
    config.read('./config/concourse.ini')
    save_path = './fly'
    #Donwload the fly package
    if not os.path.exists("./fly"):
        print("Downloading fly package ...")
        url = f"{config.get('config', 'concourse_url')}/api/v1/cli?arch=amd64&platform=linux"
        urllib.request.urlretrieve(url, save_path)
    os.chmod(save_path, 0o755)
    landscape_name = get_landscape_name()
    port = random.randint(20000,60000)
    print(f"https://concourse.cf.eu12.hana.ondemand.com/login?fly_port={port}") 
    token = input("Plase paste token: ").split()[1]
    data = {"targets": {"ci": {"api":"https://concourse.cf.eu12.hana.ondemand.com", "team":f"{team_name}", "token": {"type": "bearer", "value": token}}}}

    yaml.dump(data, open(f"{os.environ.get('HOME')}/.flyrc", "w"),default_flow_style=False)

    with open("./config/deployment_selected", 'r') as file:
        concourse_pipeline_deployment = file.read()
    
    command = f"./fly -t ci sp -p {landscape_name}-{concourse_pipeline_deployment} -c pipeline.yml -n".split()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(result.stdout.decode('utf-8'))
    if result.returncode != 0:
        print(f"Unable to deploy the pipeline : fly -t ci sp -p {landscape_name}-{concourse_pipeline_deployment} -c pipeline.yml")
        print(result.stderr)
        sys.exit(1)


def main():
    print("\nTrigering Pipeline Builder code \n")
    non_deployment_list=['pre-validation', 'post-validation', 'apim-rt', 'landscape-config', 'validate-onboarding']
    full_deployment_list=get_deployment_list()
    deployment_list=list(set(full_deployment_list) - set(non_deployment_list))
    display=Display()
    display.print_table("Deployment List", deployment_list)
    flag=True
    while(flag):
        deployment_selected=input("\nSelect one of the deployments from the above list: ")
        if deployment_selected in deployment_list:
            print(f"Generating Lifecycle for {deployment_selected}")
            flag=False
        else:
            print("Error: Input proper deployment name")
    set_deployment(deployment_selected)
    team_name = get_team_name()
    deployment_stages=generate_pipeline(deployment_selected, full_deployment_list, team_name)
    display.display_deployment_flow(deployment_stages)
    print("\nPipeline Generated Successfully : pipeline.yml")
    check = input("Do you want to deploy the pipeline Y/N : ")
    if check in ["Y", "y"]:
        deploy_pipeline(team_name)
if __name__ == "__main__":
    main()
