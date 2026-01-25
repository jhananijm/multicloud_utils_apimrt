import unittest
from unittest.mock import patch
from apimrt.clouds.aws.aws_meta import AwsMeta

class AwsMetaTestCase(unittest.TestCase):
    
    @patch('apimrt.clouds.aws.aws_meta.requests.get')
    def test_get_region(self, mock_get):
        mock_get.return_value.text = 'us-east-1'
        aws_meta = AwsMeta()
        result = aws_meta.get_region()        
        self.assertEqual(result, 'us-east-1')

    @patch('apimrt.clouds.aws.aws_meta.requests.get')
    def test_get_project_name(self, mock_get):
        mock_get.return_value.text = 'my-project'        
        aws_meta = AwsMeta()        
        result = aws_meta.get_project_name()
        self.assertEqual(result, 'my-project')
    
    @patch('apimrt.clouds.aws.aws_meta.AwsUtil.get_secrets')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_project_name')
    def test_get_secrets(self, mock_secret, mock_project, mock_region):
        mock_region.return_value.text = 'us-east-1'
        mock_project.return_value.text = 'my-project'        
        mock_secret.return_value = 'my-secret'        
        aws_meta = AwsMeta()
        result = aws_meta.get_secrets()
        # self.assertEqual(result, 'my-secret')

    @patch('apimrt.clouds.aws.aws_meta.requests.get')
    def test_get_instance_profile_name(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {'InstanceProfileArn': 'arn:aws:iam::1234567890:instance-profile/my-instance-profile'}        
        aws_meta = AwsMeta()        
        result = aws_meta.get_instance_profile_name()        
        self.assertEqual(result, 'my-instance-profile')

    @patch('apimrt.clouds.aws.aws_meta.AwsUtil.get_instance_profile')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_instance_profile_name')
    @patch('apimrt.clouds.aws.aws_meta.requests.get')
    def test_get_role_name(self, mock_instance_profile, mock_region, mock_instance_profile_name, mock_get):
        mock_region.return_value.text = 'us-east-1'
        mock_instance_profile_name.return_value = 'my-instance-profile'
        mock_instance_profile.return_value = 'my-role'        
        aws_meta = AwsMeta()        
        result = aws_meta.get_role_name()        
        # self.assertEqual(result, 'my-role')

    @patch('apimrt.clouds.aws.aws_meta.AwsUtil.get_attached_policy_paginator')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_role_name')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    def test_get_policy_map(self, mock_get_role_name, mock_attached_policy_paginator, mock_region):
        mock_region.return_value.text = 'us-east-1'
        mock_role_name = 'my-role'
        mock_response = {
            'AttachedPolicies': [
                {'PolicyName': 'policy1'},
                {'PolicyName': 'policy2'}
            ]
        }
        mock_get_role_name.return_value = mock_role_name
        mock_attached_policy_paginator.return_value.paginate.return_value = [mock_response]
        aws_meta = AwsMeta()        
        result = aws_meta.get_policy_map()        
        expected_policy_map = {'my-role': [{'PolicyName': 'policy1'}, {'PolicyName': 'policy2'}]}
        # self.assertEqual(result, expected_policy_map)

    @patch('apimrt.clouds.aws.aws_meta.AwsUtil.get_policy_document')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_policy_map')
    def test_get_available_permissions(self, mock_get_policy_map, mock_get_region, mock_policy_document):
        mock_get_region.return_value = 'us-east-1'
        mock_get_policy_map.return_value = {'my-role': [{'PolicyArn': 'policy-arn'}]}
        mock_policy_document.return_value = {
            'Statement': [
                {'Effect': 'Allow','Action': ['ec2:DescribeInstances'],'Resource': 'arn:aws:ec2:::*'},
                {'Effect': 'Allow','Action': ['sqs:SendMessage'],'Resource': 'arn:aws:sqs:::*'}
            ]
        }
        aws_meta = AwsMeta()        
        result = aws_meta.get_available_permissions()
        expected_permissions = ['ec2:DescribeInstances', 'sqs:SendMessage']
        self.assertEqual(result, expected_permissions)

    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_project_name')
    def test_get_project_secret_name(self, mock_get_project_name):
        mock_get_project_name.return_value = "my-project"
        aws_meta = AwsMeta()
        secret_name = aws_meta.get_project_secret_name()
        expected_secret_name = "my-project-secret"
        self.assertEqual(secret_name, expected_secret_name)

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.update_secrets')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_project_secret_name')
    def test_update_secrets(self, mock_get_project_secret_name, mock_get_region, mock_update_secrets):
        mock_get_project_secret_name.return_value = "my-project-secret"
        mock_get_region.return_value = "us-west-2"
        aws_meta = AwsMeta()
        result = aws_meta.update_secrets("secret1", "value1", "my-project-secret")
    
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_asg_list_by_tag')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_project_name')
    def test_get_scaling_groups(self, mock_get_project_name, mock_get_region, mock_get_asg_list_by_tag):
        mock_get_project_name.return_value = "my-project"
        mock_get_region.return_value = "us-west-2"
        mock_get_asg_list_by_tag.return_value = ["my-asg-1", "my-asg-2"]
        aws_meta = AwsMeta()
        scaling_groups = aws_meta.get_scaling_groups()
        expected_scaling_groups = ["my-asg-1", "my-asg-2"]

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.update_image')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_project_name')
    def test_update_image(self, mock_get_project_name, mock_get_region, mock_update_image):
        mock_get_project_name.return_value = "my-project"
        mock_get_region.return_value = "us-west-2"
        mock_update_image.return_value = True
        aws_meta = AwsMeta()
        result = aws_meta.update_image("my-image-id")

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_instance_id')
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.take_snapshot')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_project_name')
    def test_take_volume_snapshot(self, mock_get_project_name, mock_get_region, mock_get_instance_id, mock_take_snapshot):
        mock_get_project_name.return_value = "project_name"
        mock_get_region.return_value = "us-west-2"
        mock_get_instance_id.return_value = "my-instance-id"
        mock_take_snapshot.return_value = ['snapshot-id']
        aws_meta = AwsMeta()
        snapshot_id = aws_meta.take_volume_snapshot("10.0.0.1")

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_instance_name_from_private_ip')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    def test_get_instance_name(self, mock_get_region, mock_get_instance_name_from_private_ip):
        mock_get_region.return_value = "us-west-2"
        mock_get_instance_name_from_private_ip.return_value = "my-instance-name"
        aws_meta = AwsMeta()
        instance_name = aws_meta.get_instance_name("10.0.0.1", "my-project")

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_instance_name_from_private_ip')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_project_name')
    def test_get_project_instance_name(self, mock_get_project_name, mock_get_region, mock_get_instance_name_from_private_ip):
        mock_get_project_name.return_value = "my-project"
        mock_get_region.return_value = "us-west-2"
        mock_get_instance_name_from_private_ip.return_value = "my-instance-name"
        aws_meta = AwsMeta()
        instance_name = aws_meta.get_project_instance_name("10.0.0.1")

    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_instance_id')
    @patch('apimrt.clouds.aws.aws_utils.AwsUtil.get_instance_tags')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_region')
    @patch('apimrt.clouds.aws.aws_meta.AwsMeta.get_project_name')
    def test_get_instance_tags(self, mock_get_project_name, mock_get_region, mock_get_instance_tags, mock_get_instance_id):
        mock_get_project_name.return_value = "my-project"
        mock_get_region.return_value = "us-west-2"
        mock_get_instance_id.return_value = "i-1234567890abcdef0"
        mock_get_instance_tags.return_value = {'Tag1': 'Value1', 'Tag2': 'Value2'}
        aws_meta = AwsMeta()
        instance_tags = aws_meta.get_instance_tags("10.0.0.1")
        expected_tags = {'Tag1': 'Value1', 'Tag2': 'Value2'}

