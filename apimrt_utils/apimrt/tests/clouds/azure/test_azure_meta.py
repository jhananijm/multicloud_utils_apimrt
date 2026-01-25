import unittest
from apimrt.clouds.azure.azure_meta import AzureMeta
from unittest.mock import patch

class TestAzureMeta(unittest.TestCase):
    def setUp(self):
        self.name = "azure"
        self.azure_meta = AzureMeta()
    
    @patch('apimrt.clouds.azure.azure_meta.requests.get')
    def test_get_rg_name(self, mock_get):
        mock_data = {
            "compute": {
                "resourceGroupName": "my_resource_group"
            }
        }
        mock_get.return_value.json.return_value = mock_data
        rg_name = self.azure_meta.get_rg_name()
        expected_rg_name = "my_resource_group"
        self.assertEqual(rg_name, expected_rg_name)
        
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    def test_get_project_name(self, mock_get_rg_name):
        mock_get_rg_name.return_value = "my_project-rg"
        project_name = self.azure_meta.get_project_name()
        expected_project_name = "my_project"
        self.assertEqual(project_name, expected_project_name)

    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.get_secrets')
    def test_get_secrets(self, mock_get_secrets, mock_get_rg_name):
        mock_get_rg_name.return_value = "my_project-rg"
        mock_get_secrets.return_value = {'secret1': 'value1', 'secret2': 'value2'}
        secrets = self.azure_meta.get_secrets()
        expected_secrets = {'secret1': 'value1', 'secret2': 'value2'}
        self.assertEqual(secrets, expected_secrets)

    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_project_name')
    def test_get_project_secret_name(self, mock_get_project_name):
        mock_get_project_name.return_value = "my_project"
        project_secret_name = self.azure_meta.get_project_secret_name()
        expected_project_secret_name = "my_project"
        self.assertEqual(project_secret_name, expected_project_secret_name)

    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.get_scale_set_name_list')
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    def test_get_scaling_groups(self, mock_get_rg_name, mock_get_scale_set_name_list):
        mock_get_rg_name.return_value = "test_rg"
        mock_get_scale_set_name_list.return_value = [
            "scale_set_1", "scale_set_2", "scale_set_3"
        ]
        scaling_groups = self.azure_meta.get_scaling_groups()
        self.assertEqual(scaling_groups, ["scale_set_1", "scale_set_2", "scale_set_3"])

    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.update_image')
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    def test_update_image(self, mock_get_rg_name, mock_update_image):
        mock_get_rg_name.return_value = "test_rg"
        mock_update_image.return_value = True
        result = self.azure_meta.update_image("image123")
        self.assertTrue(result)

    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.get_instance_name_from_ip')
    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.take_volume_snapshot')
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    def test_take_volume_snapshot(self, mock_get_rg_name, mock_get_instance_name_from_ip, mock_take_volume_snapshot):
        mock_get_rg_name.return_value = "test_rg"
        mock_get_instance_name_from_ip.return_value = "test_vm"
        mock_take_volume_snapshot.return_value = True
        result = self.azure_meta.take_volume_snapshot("10.0.0.1")
        self.assertTrue(result)

    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.get_instance_name_from_ip')
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    def test_get_instance_name(self, mock_get_rg_name, mock_get_instance_name_from_ip):
        mock_get_rg_name.return_value = "test_rg"
        mock_get_instance_name_from_ip.return_value = "test_instance"
        instance_name = self.azure_meta.get_instance_name("10.0.0.1", "test_project")
        self.assertEqual(instance_name, "test_instance")

    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.get_instance_name_from_ip')
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    def test_get_project_instance_name(self, mock_get_rg_name, mock_get_instance_name_from_ip):
        mock_get_rg_name.return_value = "test_rg"
        mock_get_instance_name_from_ip.return_value = "test_instance"
        instance_name = self.azure_meta.get_project_instance_name("10.0.0.1")
        self.assertEqual(instance_name, "test_instance")

    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.get_instance_name_from_ip')
    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.get_instance_tags')
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    def test_get_instance_tags(self, mock_get_rg_name, mock_get_instance_tags, mock_get_instance_name_from_ip):
        mock_get_rg_name.return_value = "test_rg"
        mock_get_instance_name_from_ip.return_value = "test_instance"
        mock_get_instance_tags.return_value = {"tag1": "value1", "tag2": "value2"}
        instance_tags = self.azure_meta.get_instance_tags("10.0.0.1")
        self.assertEqual(instance_tags, {"tag1": "value1", "tag2": "value2"})

    @patch('apimrt.clouds.azure.azure_meta.AzureUtil.update_secrets')
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_project_name')
    @patch('apimrt.clouds.azure.azure_meta.AzureMeta.get_rg_name')
    def test_update_secrets(self, mock_get_rg_name, mock_update_secrets):
        mock_get_rg_name.return_value = "my_project-rg"
        project_name = self.azure_meta.get_project_name()
        result = self.azure_meta.update_secrets{'key1': 'value1', 'key2': 'value2'}