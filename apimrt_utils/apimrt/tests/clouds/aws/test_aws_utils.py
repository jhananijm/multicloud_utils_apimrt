import unittest
from unittest import mock
from unittest.mock import patch, MagicMock
from apimrt.clouds.aws.aws_utils import AwsUtil,Arn
from apimrt.tests.clouds.aws.common_utils import get_mock_json
import boto3
from botocore.exceptions import ClientError
import datetime
import time
from freezegun import freeze_time

class ArnTestCase(unittest.TestCase):
    def test_arn_parse(self):
        result = Arn.arn_parse("arn:aws:s3:::my-bucket")
        expected_result = Arn(
            partition="aws",service="s3",region = None,account_id=None,resource_type=None,resource="my-bucket")
        self.assertEqual(result.partition, expected_result.partition)
        self.assertEqual(result.service, expected_result.service)
        self.assertEqual(result.region, expected_result.region)
        self.assertEqual(result.account_id, expected_result.account_id)
        self.assertEqual(result.resource_type, expected_result.resource_type)
        self.assertEqual(result.resource, expected_result.resource)

    def test_parse_resource(self):
        resource_type, parsed_resource = Arn._parse_resource("resource:sub-resource")
        self.assertEqual(resource_type, "resource")
        self.assertEqual(parsed_resource, "sub-resource")

        resource = "sub-resource"
        resource_type, parsed_resource = Arn._parse_resource(resource)
        expected_resource_type = None
        expected_parsed_resource = "sub-resource"
        self.assertEqual(resource_type, expected_resource_type)
        self.assertEqual(parsed_resource, expected_parsed_resource)

    def test_arn_parse(self):
        # Test case 1: Valid ARN with known service (resource_type is None)
        parsed_arn = Arn.arn_parse("arn:aws:s3:::bucket-name")
        self.assertEqual(parsed_arn.service, "s3")
        self.assertEqual(parsed_arn.resource, "bucket-name")
        self.assertEqual(parsed_arn.resource_type, None)

        # Test case 2: Valid ARN with unknown service (resource_type is parsed)
        parsed_arn = Arn.arn_parse("arn:aws:custom:us-west-2:1234567890:resource:sub-resource")
        self.assertEqual(parsed_arn.service, "custom")
        self.assertEqual(parsed_arn.resource, "sub-resource")
        self.assertEqual(parsed_arn.resource_type, "resource")

        # Test case 3: Invalid ARN (does not start with 'arn:')
        with self.assertRaises(ValueError):
            Arn.arn_parse("invalid:arn:format")

class AwsUtilTestCase(unittest.TestCase):

    def setUp(self):
        self.region = 'us-west-2'
        self.aws_util = AwsUtil(region=self.region)

    @mock.patch('boto3.client')
    def test_get_client(self, mock_client):
        mock_test_client = mock.MagicMock()
        mock_client.return_value = mock_test_client
        result = self.aws_util.get_client('ec2')
        self.assertEqual(result,mock_test_client)

    @mock.patch('boto3.resource')
    def test_get_resource(self, mock_resource):
        mock_test_resource = mock.MagicMock()
        mock_resource.return_value = mock_test_resource
        result = self.aws_util.get_resource('ec2')
        self.assertEqual(result,mock_test_resource)

    @mock.patch('boto3.client')
    def test_complete_lifecycle_action_success(self, mock_client):
        mock_autoscaling_client = mock.MagicMock()
        mock_autoscaling_client.complete_lifecycle_action.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_client.return_value = mock_autoscaling_client
        result = self.aws_util.complete_lifecycle_action(
            'LifecycleHookName','AutoScalingGroupName','i-1234567890abcdef0','LifecycleActionToken','CONTINUE')
        self.assertTrue(result)

    @mock.patch('boto3.client')
    def test_complete_lifecycle_action_error(self, mock_client):
        mock_autoscaling_client = mock.MagicMock()
        mock_autoscaling_client.complete_lifecycle_action.side_effect = Exception('TestError')
        mock_client.return_value = mock_autoscaling_client
        result = self.aws_util.complete_lifecycle_action(
            'LifecycleHookName','AutoScalingGroupName','i-1234567890abcdef0','my-action-token','CONTINUE')
        self.assertFalse(result)

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instance_ip_success(self, mock_client):
        mock_ec2_client = mock.MagicMock()
        mock_ec2_client.describe_instances.return_value = get_mock_json('instance')
        mock_client.return_value = mock_ec2_client
        result = self.aws_util.get_instance_ip('i-0925440737cc9da2d')
        self.assertEqual(result, {'Status': True, 'ip_address': '192.168.12.104'})

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instance_ip_no_instances(self, mock_client):
        mock_ec2_client = mock.MagicMock()
        mock_ec2_client.describe_instances.return_value = get_mock_json('no_instance')
        mock_client.return_value = mock_ec2_client
        result = self.aws_util.get_instance_ip('i-0925440737cc9da2d')
        self.assertEqual(result, {'Status': False})
    
    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instance_ip_error(self, mock_client):
        mock_ec2_client = mock.MagicMock()
        mock_ec2_client.describe_instances.side_effect = Exception('TestError')
        mock_client.return_value = mock_ec2_client
        result = self.aws_util.get_instance_ip('i-0925440737cc9da2d')
        self.assertEqual(result, {'Status': False})

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instance_id_success(self, mock_client):
        mock_ec2_client = mock.MagicMock()
        mock_ec2_client.describe_instances.return_value = get_mock_json('instance')
        mock_client.return_value = mock_ec2_client
        result = self.aws_util.get_instance_id('192.168.12.104', 'project_name')
        self.assertEqual(result, 'i-0925440737cc9da2d')

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instance_id_no_instances(self, mock_client):
        mock_ec2_client = mock.MagicMock()
        mock_ec2_client.describe_instances.return_value = get_mock_json('no_instance')
        mock_client.return_value = mock_ec2_client
        result = self.aws_util.get_instance_id('192.168.12.104', 'project_name')
        self.assertIsNone(result)

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_asg_data(self, mock_client):
        asg_data = [{'Name': 'asg_name', 'MinSize': 1, 'MaxSize': 3}]
        mock_asg_client = mock.MagicMock()
        mock_asg_client.describe_auto_scaling_groups.return_value = {'AutoScalingGroups': asg_data}
        mock_client.return_value = mock_asg_client
        result = self.aws_util.get_asg_data('asg_name')
        self.assertEqual(result, asg_data)
    
    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_asg_data')
    def test_get_asg_count(self, mock_get_asg_data):
        asg_data = [{'Name': 'asg_name', 'MinSize': 1, 'MaxSize': 3}]
        mock_get_asg_data.return_value = asg_data
        result = self.aws_util.get_asg_count('asg_name', 'MinSize')
        self.assertEqual(result, 1)
        
    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_asg_count')
    def test_get_asg_min_count(self, mock_get_asg_count):
        mock_get_asg_count.return_value = 1
        result = self.aws_util.get_asg_min_count('asg_name')
        self.assertEqual(result, 1)

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_asg_count')
    def test_get_asg_desired_count(self, mock_get_asg_count):
        mock_get_asg_count.return_value = 3
        result = self.aws_util.get_asg_desired_count('asg_name')
        self.assertEqual(result, 3)
    
    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_asg_data')
    def test_get_instance_len_from_asg(self, mock_get_asg_data):
        mock_get_asg_data.return_value = [{'Instances': [{}] * 5}]
        result = self.aws_util.get_instance_len_from_asg('asg_name')
        self.assertEqual(result, 5)
      
    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_asg_tags_success(self, mock_get_client):
        mock_client = mock.Mock()
        mock_client.describe_tags.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 200},
            'Tags': [{'Key': 'tag1', 'Value': 'value1'},{'Key': 'tag2', 'Value': 'value2'}]
        }
        mock_get_client.return_value = mock_client
        result = self.aws_util.get_asg_tags('auto_scaling_group_name')
        self.assertEqual(result, {'tag1': 'value1', 'tag2': 'value2'})

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_asg_tags_client_error(self, mock_get_client):
        mock_client = mock.Mock()
        mock_client.describe_tags.side_effect = ClientError({}, 'operation failed')
        mock_get_client.return_value = mock_client
        result = self.aws_util.get_asg_tags('auto_scaling_group_name')
        self.assertEqual(result, {})

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_instance')
    def test_get_instance_tags_success(self, mock_get_instance):
        mock_instance = mock.Mock()
        mock_instance.tags = [{'Key': 'tag1', 'Value': 'value1'},{'Key': 'tag2', 'Value': 'value2'}]
        mock_get_instance.return_value = mock_instance
        result = self.aws_util.get_instance_tags('i-12345')
        self.assertEqual(result, {'tag1': 'value1', 'tag2': 'value2'})

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_instance')
    def test_get_instance_tags_client_error(self, mock_get_instance):
        mock_get_instance.side_effect = ClientError({}, 'operation failed')
        result = self.aws_util.get_instance_tags('i-12345')
        self.assertEqual(result, {})

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_delete_asg_tag_success(self, mock_get_client):
        mock_client = mock.Mock()
        mock_client.delete_tags.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_get_client.return_value = mock_client
        result = self.aws_util.delete_asg_tag('auto_scaling_group_name', 'key')
        self.assertTrue(result)

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_delete_asg_tag_client_error(self, mock_get_client):
        mock_client = mock.Mock()
        mock_client.delete_tags.side_effect = ClientError({}, 'operation failed')
        mock_get_client.return_value = mock_client
        result = self.aws_util.delete_asg_tag('auto_scaling_group_name', 'key')
        self.assertFalse(result)
    
    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_create_asg_tag_success(self, mock_get_client):
        mock_client = mock.Mock()
        mock_client.create_or_update_tags.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_get_client.return_value = mock_client
        result = self.aws_util.create_asg_tag('auto_scaling_group_name', 'key', 'value', True)
        self.assertTrue(result)

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_create_asg_tag_client_error(self, mock_get_client):
        mock_client = mock.Mock()
        mock_client.create_or_update_tags.side_effect = ClientError({}, 'operation failed')
        mock_get_client.return_value = mock_client
        result = self.aws_util.create_asg_tag('auto_scaling_group_name', 'key', 'value', True)
        self.assertFalse(result)

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_invoke_lambda_success(self, mock_get_client):
        payload = {'key': 'value'}
        mock_client = mock.Mock()
        mock_client.invoke.return_value = {'StatusCode': 200}
        mock_get_client.return_value = mock_client
        result = self.aws_util.invoke_lambda('function_name', payload, 'Event')
        self.assertEqual(result, {'StatusCode': 200})

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_invoke_lambda_client_error(self, mock_get_client):
        payload = {'key': 'value'}
        mock_client = mock.Mock()
        mock_client.invoke.side_effect = ClientError({}, 'operation failed')
        mock_get_client.return_value = mock_client
        result = self.aws_util.invoke_lambda('function_name', payload, 'Event')
        self.assertIsNone(result)

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_secrets_success(self, mock_get_client):
        mock_client = mock.Mock()
        mock_client.get_secret_value.return_value = {'SecretString': '{"key": "value"}'}
        mock_get_client.return_value = mock_client
        result = self.aws_util.get_secrets('secret_id')
        self.assertEqual(result, {'key': 'value'})

    @mock.patch("boto3.client")
    def test_get_secrets_binary_success(self, mock_client):
        response = {'SecretBinary': b'{"key": "value"}'}
        mock_client.return_value.get_secret_value.return_value = response
        result = self.aws_util.get_secrets('secret_id')
        self.assertEqual(result, {"key": "value"})

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instances_id_from_ag_success(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.describe_auto_scaling_groups.return_value = get_mock_json('asg')
        result = self.aws_util.get_instances_id_from_ag('ag_name')
        expected = ['i-12345678', 'i-87654321']
        self.assertEqual(result, expected)

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instances_id_from_ag_no_group_found(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.describe_auto_scaling_groups.return_value = {}
        result = self.aws_util.get_instances_id_from_ag('nonexistent-group')
        self.assertEqual(result, [])

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_resource')
    def test_get_instance_success(self, mock_get_resource):
        mock_instance = mock_get_resource.return_value.Instance.return_value
        result = self.aws_util.get_instance('i-1234567890abcdefg')
        self.assertEqual(result, mock_instance)

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_instance')
    def test_get_instance_private_ip_success(self, mock_get_instance):
        mock_instance = mock_get_instance.return_value
        mock_instance.private_ip_address = '10.0.0.1'
        result = self.aws_util.get_instance_private_ip('i-1234567890abcdefg')
        self.assertEqual(result, '10.0.0.1')

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instance_name_from_private_ip_success(self, mock_get_client):
        mock_ec2_client = mock_get_client.return_value
        mock_response = get_mock_json('instance')
        mock_ec2_client.describe_instances.return_value = mock_response
        result = self.aws_util.get_instance_name_from_private_ip('192.168.12.104', 'dt-dev-landscape')
        self.assertEqual(result, 'dt-dev-landscape_ZKCS1')

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instances_from_asg_success(self, mock_get_client):
        mock_ec2_client = mock_get_client.return_value
        mock_response = get_mock_json('asg_instance')
        mock_ec2_client.describe_instances.return_value = mock_response
        result = self.aws_util.get_instances_from_asg("my-asg")       
        self.assertEqual(result, ['i-1234567890abcdef0', 'i-1234567890abcdef0'])

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_resource')
    def test_upload_to_s3(self, mock_get_resource):
        mock_resource = MagicMock()
        mock_upload_file = MagicMock()
        mock_resource.meta.client.upload_file = mock_upload_file
        mock_get_resource.return_value = mock_resource
        self.aws_util.upload_to_s3('/tests/clouds/aws/mock_data/asg.json', 'bucket_name', 'key')

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_resource')
    def test_download_from_s3(self, mock_get_resource):
        mock_resource = MagicMock()
        mock_download_file = MagicMock()
        mock_get_resource.return_value = mock_resource
        mock_resource.meta.client.download_file = mock_download_file
        result = self.aws_util.download_from_s3('bucket_name', 'key', '/tests/clouds/aws/mock_data/asg.json')
        self.assertEqual(result, '/tests/clouds/aws/mock_data/asg.json')

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_asg_list_by_tag(self, mock_client):
        mock_asg_response = get_mock_json('asg_tags')
        mock_client.return_value.describe_auto_scaling_groups.return_value = mock_asg_response
        result = self.aws_util.get_asg_list_by_tag('tag_key', 'tag_value')
        self.assertEqual(result, ['ASG1', 'ASG3'])

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_secret_list_by_tag(self, mock_client):
        mock_secret_response = {'SecretList': [{'Name': 'Secret1'},{'Name': 'Secret2'}]}
        mock_client.return_value.list_secrets.return_value = mock_secret_response
        result = self.aws_util.get_secret_list_by_tag('tag_key', 'tag_value')
        self.assertEqual(result, ['Secret1', 'Secret2'])
        mock_secret_response_empty = {'SecretList': []}
        mock_client.return_value.list_secrets.return_value = mock_secret_response_empty
        result_empty = self.aws_util.get_secret_list_by_tag('tag_key', 'tag_value')
        self.assertEqual(result_empty, [])

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_resources_by_tag(self, mock_client):
        mock_resource_response = {
            'ResourceTagMappingList': [{'ResourceARN': 'arn:aws:resource1'},{'ResourceARN': 'arn:aws:resource2'}]}
        mock_client.return_value.get_resources.return_value = mock_resource_response
        with self.assertRaises(IndexError):
            self.aws_util.get_resources_by_tag('tag_key', 'tag_value', 'resource_type')

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_resources_by_tag')
    def test_get_s3_list_by_tag(self, mock_get_resources_by_tag):
        mock_resource_list = ['s3_bucket1', 's3_bucket2']
        mock_get_resources_by_tag.return_value = mock_resource_list
        result = self.aws_util.get_s3_list_by_tag('tag_key', 'tag_value')
        self.assertEqual(result, mock_resource_list)

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_resources_by_tag')
    def test_get_lambda_list_by_tag(self, mock_get_resources_by_tag):
        mock_resource_list = ['lambda_function1', 'lambda_function2']
        mock_get_resources_by_tag.return_value = mock_resource_list
        result = self.aws_util.get_lambda_list_by_tag('tag_key', 'tag_value')
        self.assertEqual(result, mock_resource_list)

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_lambda_env_dict(self, mock_get_client):
        mock_environment = {'Variable1': 'value1','Variable2': 'value2'}
        mock_function_response = {'Configuration': {'Environment': {'Variables': mock_environment}}}
        mock_client = mock_get_client.return_value
        mock_client.get_function.return_value = mock_function_response
        result = self.aws_util.get_lambda_env_dict('func_name')
        self.assertEqual(result, mock_environment)

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_asg_data')
    def test_get_launch_configuration_from_asg(self, mock_get_asg_data, mock_get_client):
        mock_launch_configurations = [{'LaunchConfigurationName': 'launch_config1',}]
        mock_get_asg_data.return_value = [{'LaunchConfigurationName': 'launch_config1'}]
        mock_client = mock_get_client.return_value
        mock_client.describe_launch_configurations.return_value = {'LaunchConfigurations': mock_launch_configurations}
        result = self.aws_util.get_launch_configuration_from_asg('asg_name')
        expected_result = mock_launch_configurations
        self.assertEqual(result['LaunchConfigurations'], expected_result)

    @freeze_time("2022-01-01 12:00:00")
    def test_generate_launch_config_name(self):
        with patch('apimrt.clouds.aws.aws_utils.datetime') as mock_datetime, patch('apimrt.clouds.aws.aws_utils.time') as mock_time:
            mock_datetime.now.return_value.strftime.return_value = "20220101"
            mock_time.time.return_value = 1641024000
            result = self.aws_util.generate_launch_config_name('asg_name', 'image_id')
        self.assertEqual(result, "asg_name-image_id-20220101-1641024000")

    @patch('apimrt.clouds.aws.aws_utils.base64')
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_create_launch_configuration(self, mock_get_client, mock_base64):
        launch_config = get_mock_json('launch_config')
        mock_base64.b64decode.return_value.decode.return_value = "decoded_user_data"
        result = self.aws_util.create_launch_configuration(launch_config)
        self.assertEqual(result, launch_config["LaunchConfigurationName"])

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_asg_list_by_tag')
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_launch_configuration_from_asg')
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.generate_launch_config_name')
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.create_launch_configuration')
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.update_launch_config')
    def test_update_image(self, mock_update_launch_config, mock_create_launch_configuration,
                          mock_generate_launch_config_name, mock_get_launch_configuration_from_asg,
                          mock_get_asg_list_by_tag):
        asg_list = ["asg1", "asg2"]
        mock_get_asg_list_by_tag.return_value = asg_list
        mock_get_launch_configuration_from_asg.return_value = get_mock_json('lc_update')
        mock_generate_launch_config_name.return_value = "new_launch_config"
        mock_create_launch_configuration.return_value = "new_launch_config"
        mock_update_launch_config.return_value = True
        result = self.aws_util.update_image('project_name', 'image_id')
        self.assertEqual(result, ["asg1","asg2"])

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_take_snapshot(self,mock_client):
        mock_client = mock_client.return_value
        mock_client.create_snapshots.return_value = get_mock_json('snapshot')
        result = self.aws_util.take_snapshot('instance_id', 'project')
        self.assertEqual(result, ['snapshot1', 'snapshot2'])
    
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_instance_profile(self, mock_client):
        instance_profile_name = "instance_profile_name"
        mock_client = mock_client.return_value
        mock_client.get_instance_profile.return_value = {'InstanceProfileName': instance_profile_name}
        result = self.aws_util.get_instance_profile(instance_profile_name)
        self.assertEqual(result, {'InstanceProfileName': instance_profile_name})

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_attached_policy_paginator(self, mock_client):
        mock_client = mock_client.return_value
        mock_paginator = mock_client.get_paginator.return_value
        result = self.aws_util.get_attached_policy_paginator()
        self.assertEqual(result, mock_paginator)

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_get_policy_document(self, mock_client):
        mock_client = mock_client.return_value
        policy_response = {'Policy': {'DefaultVersionId': 'your_version_id'}}
        version_response = {'PolicyVersion': {'Document': 'your_policy_document'}}
        mock_client.get_policy.return_value = policy_response
        mock_client.get_policy_version.return_value = version_response
        result = self.aws_util.get_policy_document('policyarn')
        self.assertEqual(result, 'your_policy_document')

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_update_launch_config(self,mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.describe_auto_scaling_groups.return_value = {
            "AutoScalingGroups": [{"LaunchConfigurationName": 'launch_config_name'}]}
        result = self.aws_util.update_launch_config('asg_name', 'launch_config_name')
        self.assertTrue(result)

    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    @mock.patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_secrets')
    def test_update_secrets(self, mock_get_secrets, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_get_secrets.return_value = {"existing_key": "existing_value"}
        mock_client.update_secret = MagicMock()
        updated_secrets = self.aws_util.update_secrets("new_key", "new_value", "test_secret")

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_check_for_scalein_not_scale_in(self, mock_client):
        mock_response = get_mock_json('not_scale_in')
        mock_client.return_value.describe_scaling_activities.return_value = mock_response
        result = self.aws_util.check_for_scalein("asg_name", "i-1234567890abcdef")
        self.assertEqual(result, 'not-scale-in')
    
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_check_for_scalein_scale_in(self, mock_client):
        mock_response = get_mock_json('scale_in')
        mock_client.return_value.describe_scaling_activities.return_value = mock_response
        result = self.aws_util.check_for_scalein('asg_name', 'i-1234567890abcdef')
        self.assertEqual(result, 'scale-in')

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_client')
    def test_check_for_scalein_exception(self, mock_client):
        mock_client.return_value.describe_scaling_activities.side_effect = Exception('Something went wrong')
        result = self.aws_util.check_for_scalein('asg_name', 'i-1234567890abcdef')
        self.assertFalse(result)
    


    