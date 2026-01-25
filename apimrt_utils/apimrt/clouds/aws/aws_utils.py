import base64
import boto3
from botocore.exceptions import ClientError, WaiterError
from typing import Any, Dict, List, Optional, Union
import json
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)


# logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

class Arn(object):
    def __init__(self, partition, service, region, account_id, resource_type, resource):
        """

        Args:
            partition:
            service:
            region:
            account_id:
            resource_type:
            resource:
        """
        self.partition = partition
        self.service = service
        self.region = region
        self.account_id = account_id
        self.resource_type = resource_type
        self.resource = resource

    @staticmethod
    def _parse_resource(resource):
        first_separator_index = -1
        for idx, c in enumerate(resource):
            if c in (':', '/'):
                first_separator_index = idx
                break

        if first_separator_index != -1:
            resource_type = resource[:first_separator_index]
            resource = resource[first_separator_index + 1:]
        else:
            resource_type = None

        return resource_type, resource

    @classmethod
    def arn_parse(cls, arn):
        if not arn.startswith('arn:'):
            raise ValueError
        elements = arn.split(':', 5)
        service = elements[2]
        resource = elements[5]
        str_to_none = lambda x: None if x == '' else x

        if service in ['s3', 'sns', 'apigateway', 'execute-api']:
            resource_type = None
        else:
            resource_type, resource = cls._parse_resource(resource)

        return cls(
            partition=elements[1],
            service=service,
            region=str_to_none(elements[3]),
            account_id=str_to_none(elements[4]),
            resource_type=resource_type,
            resource=resource,
        )

class AwsUtil:
    def __init__(self, region=None):
        self.region = region

    def get_client(self, client_type):
        """

        :param client_type:
        :return:
        """
        return boto3.client(client_type, self.region)

    def get_resource(self, client_type):
        """

        :param client_type:
        :return:
        """
        return boto3.resource(client_type, self.region)

    def complete_lifecycle_action(self, LifecycleHookName: str, AutoScalingGroupName: str, EC2InstanceId: str,
                                  LifecycleActionToken: str,
                                  LifecycleActionResult: str = 'CONTINUE') -> bool:
        """

        :param LifecycleHookName:
        :param AutoScalingGroupName:
        :param EC2InstanceId:
        :param LifecycleActionToken:
        :param LifecycleActionResult:
        :return:
        """

        try:
            client = self.get_client('autoscaling')
            response = client.complete_lifecycle_action(LifecycleHookName=LifecycleHookName,
                                                        AutoScalingGroupName=AutoScalingGroupName,
                                                        InstanceId=EC2InstanceId,
                                                        LifecycleActionToken=LifecycleActionToken,
                                                        LifecycleActionResult=LifecycleActionResult)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return True
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return False

    def get_instance_ip(self, EC2InstanceId: str) -> Dict[str, Any]:
        """
        :param EC2InstanceId:
        :return:
        """
        try:
            client = self.get_client('ec2')
            response = client.describe_instances(InstanceIds=[EC2InstanceId])
            if response['ResponseMetadata']['HTTPStatusCode'] == 200 and len(response['Reservations']) != 0:
                return {'Status': True,
                        'ip_address': response['Reservations'][0]['Instances'][0]['PrivateIpAddress']}
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except KeyError as e:
            logger.error(f"KeyError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return {'Status': False}

    def get_instance_id(self, instance_ip: str, project: str) -> str:

        try:
            client = self.get_client('ec2')
            instances = client.describe_instances(
                Filters=[
                    {
                        'Name': 'private-ip-address',
                        'Values': [instance_ip]
                    },
                    {
                        'Name': 'tag:Project',
                        'Values': [project]
                    }
                ]
            )
            if instances['Reservations']:
                return instances['Reservations'][0]['Instances'][0]['InstanceId']
            else:
                print('No instances found.')
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e

    def get_asg_data(self, asg_name: str) -> List[Any]:
        """

        :param asg_name:
        :return:
        """
        try:
            asg_client = self.get_client('autoscaling')
            asg_data_from_boto = asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name])
            return asg_data_from_boto['AutoScalingGroups']
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            return []

    def get_asg_count(self, asg_name: str, count_type: str) -> Optional[int]:
        """

        :param asg_name:
        :param count_type:
        :return:
        """
        asg_data_list = self.get_asg_data(asg_name)
        if len(asg_data_list) != 0:
            return asg_data_list[0][count_type]

    def get_asg_min_count(self, asg_name: str) -> Optional[int]:
        """

        :param asg_name:
        :return:
        """
        return self.get_asg_count(asg_name, 'MinSize')

    def get_asg_desired_count(self, asg_name: str) -> Optional[int]:
        """

        :param asg_name:
        :return:
        """
        return self.get_asg_count(asg_name, 'DesiredCapacity')

    def get_instance_len_from_asg(self, asg_name: str) -> int:
        """

        :param asg_name:
        :return:
        """
        asg_data_list = self.get_asg_data(asg_name)
        logger.info(asg_data_list)
        return len(asg_data_list[0]['Instances'])

    def check_for_scalein(self, AutoScalingGroupName: str, EC2InstanceId: str) -> Union[str, bool]:
        """

        :param AutoScalingGroupName:
        :param EC2InstanceId:
        :return:
        """
        try:
            client = self.get_client('autoscaling')
            response = client.describe_scaling_activities(
                AutoScalingGroupName=AutoScalingGroupName
            )
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                for each_activity in response['Activities']:
                    if EC2InstanceId in each_activity['Description'] and 'terminated or stopped.' in each_activity['Cause']:
                        return 'not-scale-in'
                    else:
                        return 'scale-in'
                return True
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return False

    def get_asg_tags(self, AutoScalingGroupName: str) -> Dict[str, Any]:
        """

        :param AutoScalingGroupName:
        :param Key:
        :return:
        """
        try:
            client = self.get_client('autoscaling')
            tag_dict = {}
            response = client.describe_tags(
                Filters=[{'Name': 'auto-scaling-group', 'Values': [AutoScalingGroupName]}])
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                for data in response['Tags']:
                    tag_dict[data['Key']] = data['Value']
            return tag_dict
        except ClientError as e:
            logger.error(f"Unexpected error: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return {}

    def get_instance_tags(self, instanceid: str) -> Dict[str, Any]:
        """
        :param instanceid:
        :return:
        """
        try:
            instance = self.get_instance(instanceid)
            return {tag['Key']: tag['Value'] for tag in instance.tags}
        except ClientError as e:
            logger.error(f"Unexpected error: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return {}

    def delete_asg_tag(self, AutoScalingGroupName: str, Key: str) -> bool:
        """
        :param AutoScalingGroupName:
        :param Key:
        :return:
        """
        try:
            client = self.get_client('autoscaling')
            response = client.delete_tags(Tags=[{
                'ResourceId': AutoScalingGroupName,
                'ResourceType': 'auto-scaling-group',
                'Key': Key}])
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return True
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return False

    def create_asg_tag(self, AutoScalingGroupName, Key, value, PropagateAtLaunch) -> bool:
        """
        :param AutoScalingGroupName:
        :param Key:
        :param value:
        :param PropagateAtLaunch:
        :return:
        """
        try:
            client = self.get_client('autoscaling')
            response = client.create_or_update_tags(Tags=[{
                'ResourceId': AutoScalingGroupName,
                'ResourceType': 'auto-scaling-group',
                'Key': Key,
                'Value': value,
                'PropagateAtLaunch': PropagateAtLaunch}])
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return True
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return False

    def invoke_lambda(self, function_name: str, payload: Dict[str, Any], invocation_type: str = 'Event') -> Any:
        """
        :param function_name:
        :param payload:
        :param invocation_type:
        :return:
        """
        try:
            client = self.get_client('lambda')
            return client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload),
            )
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e

    def get_secrets(self, secret_id: str) -> Dict[str, Any]:
        '''
        :param secret_id:secrets manager name
        :return: secrets as json payload
        '''
        try:
            client = self.get_client('secretsmanager')
            resp = client.get_secret_value(SecretId=secret_id)
            if 'SecretString' in resp:
                secret = resp['SecretString']
                return json.loads(secret)
            else:
                decoded_binary_secret = resp['SecretBinary']
                return json.loads(decoded_binary_secret)
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return {}

    def get_instances_id_from_ag(self, ag_name: str) -> List[str]:
        """
        :param ag_name: provide the autoscaling group name
        :return: returns the list of instance id
        """
        try:
            client = self.get_client('autoscaling')
            res = client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[ag_name])
            return [inst_dict['InstanceId'] for inst_dict in res['AutoScalingGroups'][0]['Instances']]
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e
        return []

    def get_instance(self, instance_id: str):
        """
        :param instance_id:
        :return:
        """
        try:
            ec2 = self.get_resource('ec2')
            return ec2.Instance(instance_id)
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e

    def get_instance_private_ip(self, instance_id: str) -> str:
        """
        :param instance_id:
        :return: instance private ip address
        """
        try:
            instance = self.get_instance(instance_id)
            return instance.private_ip_address
        except ClientError as e:
            logger.error(f"ClientError: {e}")
            raise e
        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e

    def get_instance_name_from_private_ip(self, ip, project_name) -> str:
        ec2 = self.get_client("ec2")
        try:
            response = ec2.describe_instances(Filters=[
                {
                    'Name': 'private-ip-address',
                    'Values': [ip]
                },
                {
                    'Name': 'tag:Project',
                    'Values': [project_name]
                }
            ])
            if response['Reservations']:
                tags = response['Reservations'][0]['Instances'][0]['Tags']
                for tag in tags:
                    if tag['Key'] == 'Name':
                        return tag['Value']
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp


    def get_instances_from_asg(self, asg: str) -> List[str]:
        ec2 = self.get_client("ec2")
        instance_ids: List[str] = []
        response = ec2.describe_instances(
            Filters=[ 
                {
                    "Name": "tag:aws:autoscaling:groupName",
                    "Values": [asg],
                }
            ]
        )
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance_ids.append(instance["InstanceId"])
        return instance_ids

    def upload_to_s3(self, filename: str, bucket_name: str, key: str):
        s3 = self.get_resource("s3")
        s3.meta.client.upload_file(filename, bucket_name, key)

    def download_from_s3(self, bucket_name: str, key: str, filename: str) -> str:
        s3 = self.get_resource("s3")
        s3.meta.client.download_file(bucket_name, key, filename)
        return filename

    def get_asg_list_by_tag(self, tag_key, tag_value) -> List:
        """
        Args:
            tag_key:
            tag_value:
        Returns:
        """
        res_list = []
        client = self.get_client('autoscaling')
        for asg in client.describe_auto_scaling_groups()['AutoScalingGroups']:
            if 'Tags' not in asg.keys():
                continue
            if len(asg['Tags']) == 0:
                continue
            for resource in asg['Tags']:
                if 'Key' not in resource.keys():
                    continue
                if resource['Key'] == tag_key and resource['Value'] == tag_value:
                    res_list.append(resource['ResourceId'])
        return res_list

    def get_secret_list_by_tag(self, tag_key, tag_value) -> List:
        """
        Args:
            tag_key:
            tag_value:
        Returns:
        """
        client = self.get_client('secretsmanager')
        resp = client.list_secrets(
            Filters=[{'Key': 'tag-key', 'Values': [tag_key]}, {'Key': 'tag-value', 'Values': [tag_value]}])
        if len(resp['SecretList']) == 0:
            return []
        return [secret['Name'] for secret in resp['SecretList']]

    def get_resources_by_tag(self, tag_key, tag_value, resource) -> List:
        """
        Args:
            tag_key:
            tag_value:
            resource:
        Returns:
        """
        client = self.get_client('resourcegroupstaggingapi')
        resp = client.get_resources(
            TagFilters=[
                {
                    'Key': tag_key,
                    'Values': [
                        tag_value,
                    ]
                },
            ],
            ResourcesPerPage=100,
            ResourceTypeFilters=[
                resource
            ]
        )

        return [Arn.arn_parse(resource['ResourceARN']).resource for resource in resp['ResourceTagMappingList']]

    def get_s3_list_by_tag(self, tag_key, tag_value) -> List:
        """
        Args:
            tag_key:
            tag_value:

        Returns:
        """
        return self.get_resources_by_tag(tag_key, tag_value, 's3')

    def get_lambda_list_by_tag(self, tag_key, tag_value) -> List:
        """
        Args:
            tag_key:
            tag_value:
        Returns:
        """
        return self.get_resources_by_tag(tag_key, tag_value, 'lambda')

    def get_lambda_env_dict(self, func_name):
        client = self.get_client('lambda')
        resp = client.get_function(FunctionName=func_name)
        return resp['Configuration']['Environment']['Variables']

    def upload_lambda(self, file_path):
        """
        Args:
            file_path:
        Returns:
        """
        pass

    def update_lambda_env_config(self, env_dict):
        """
        Args:
            env_dict:
        Returns:
        """
        pass

    def get_launch_configuration_from_asg(self, asg):
        """
        Args:
            asg:
        Returns:
        """
        client = self.get_client('autoscaling')
        return client.describe_launch_configurations(
            LaunchConfigurationNames=[
                self.get_asg_data(asg)[0]['LaunchConfigurationName']
            ]
        )

    def generate_launch_config_name(self, asg_name, image_id):
        """Generates and returns a launch configuration name using a specified prefix.
        The format of the resulting launch configuration name is:
        {project_name}-{image_id}-{date}-{epoch}"""
        now = datetime.now()
        date = now.strftime("%Y%m%d")
        epoch = int(time.time())
        return f"{asg_name}-{image_id}-{date}-{epoch}"

    def create_launch_configuration(self, launch_config):
        try:
            encoded_user_data = launch_config["UserData"]
            decoded_user_data = base64.b64decode(encoded_user_data).decode()
            client = self.get_client('autoscaling')
            client.create_launch_configuration(
                LaunchConfigurationName=launch_config["LaunchConfigurationName"],
                ImageId=launch_config["ImageId"],
                InstanceType=launch_config["InstanceType"],
                SecurityGroups=launch_config["SecurityGroups"],
                UserData=decoded_user_data,
                IamInstanceProfile=launch_config["IamInstanceProfile"],
                BlockDeviceMappings=launch_config["BlockDeviceMappings"],
            )
            return launch_config['LaunchConfigurationName']
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def update_launch_config(self, asg_name, launch_config_name):
        """Updates an ASG's launch configuration."""
        client = self.get_client('autoscaling')
        client.update_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            LaunchConfigurationName=launch_config_name,
        )
        while True:
            response = client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
            launch_configuration_name = response['AutoScalingGroups'][0]['LaunchConfigurationName']
            if launch_configuration_name == launch_config_name:
                break
            time.sleep(10)
        return True

    def update_image(self, project_name, image_id):
        updated_asg_list = []
        try:
            asg_list = self.get_asg_list_by_tag("Project", project_name)
            for asg in asg_list:
                launch_config = self.get_launch_configuration_from_asg(asg)['LaunchConfigurations'][0]
                launch_config['ImageId'] = image_id
                launch_config['LaunchConfigurationName'] = self.generate_launch_config_name(asg, image_id)
                new_launch_config = self.create_launch_configuration(launch_config)
                result = self.update_launch_config(asg, new_launch_config)
                if result:
                    updated_asg_list.append(asg)
            return updated_asg_list
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def take_snapshot(self, instance_id, project):
        try:
            client = self.get_client('ec2')
            response = client.create_snapshots(
                Description=f'Volume Snapshot of {instance_id}',
                InstanceSpecification={'InstanceId': instance_id, 'ExcludeBootVolume': True, },
                TagSpecifications=[{
                    'ResourceType': 'snapshot',
                    'Tags': [{'Key': 'Project', 'Value': project}, ],
                }, ], )
            snapshot_ids = []
            for i in response['Snapshots']:
                snapshot_id = i['SnapshotId']
                snapshot_ids.append(snapshot_id)
                waiter = client.get_waiter('snapshot_completed')
                waiter.wait(SnapshotIds=[snapshot_id])
            return snapshot_ids
        except WaiterError as e:
            logger.error(f"WaiterError: {e}")
            raise e

    def get_instance_profile(self, instance_profile_name):
        client = self.get_client('iam')
        return client.get_instance_profile(InstanceProfileName=instance_profile_name)

    def get_attached_policy_paginator(self):
        client = self.get_client('iam')
        return client.get_paginator('list_attached_role_policies')

    def get_policy_document(self, policyarn):
        client = self.get_client('iam')
        policy_response = client.get_policy(PolicyArn=policyarn)
        version_id = policy_response['Policy']['DefaultVersionId']
        version_response = client.get_policy_version(PolicyArn=policyarn, VersionId=version_id)
        return version_response['PolicyVersion']['Document']

    def update_secrets(self, key, value, secretname):
        try:
            client = self.get_client("secretsmanager")
            existing_secrets = self.get_secrets(secretname)
            existing_secrets.update({key: value})
            client.update_secret(
                SecretId=secretname,
                SecretString=json.dumps(existing_secrets)
            )
            return self.get_secrets(secretname)
        except Exception as excp:
            logger.error(f"UpdateFailedError: {excp}")
            raise excp
