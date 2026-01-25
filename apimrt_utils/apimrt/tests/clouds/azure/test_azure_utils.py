import unittest
from unittest.mock import patch, MagicMock
from apimrt.clouds.azure.azure_utils import AzureUtil
from datetime import timezone
from subprocess import CalledProcessError


class TestAzureUtil(unittest.TestCase):

    @patch('apimrt.clouds.azure.azure_utils.os.environ.get')
    @patch('apimrt.clouds.azure.azure_utils.subprocess.check_output')
    def test_init(self, mock_check_output, mock_environ_get):
        expected_output = b'{"id": "test_subscription_id"}'
        mock_environ_get.return_value = None
        mock_check_output.side_effect = [CalledProcessError(1, ''), expected_output]
        azure_util = AzureUtil('test_rg', 'test_subscription_id')
        self.assertEqual(azure_util.rg_name, 'test_rg')
        self.assertEqual(azure_util.subscription_id, 'test_subscription_id')

        azure_util = AzureUtil('test_rg')
        self.assertEqual(azure_util.rg_name, 'test_rg')
        self.assertEqual(azure_util.subscription_id, "test_subscription_id")

    
    @patch('azure.identity.ManagedIdentityCredential')
    @patch('azure.identity.AzureCliCredential')
    @patch('azure.identity.EnvironmentCredential')
    @patch('azure.identity.DefaultAzureCredential')
    def test_get_credential_chain(self, mock_default_cred, mock_env_cred, mock_cli_cred, mock_mgmt_cred):
        util = AzureUtil('rg_name')
        credential_chain = util.get_credential_chain()
        expected_credential_chain = [
            mock_mgmt_cred,
            mock_cli_cred,
            mock_env_cred,
            mock_default_cred
        ]
        for credential, expected_class in zip(credential_chain.credentials, expected_credential_chain):
            self.assertFalse(isinstance(credential, type(expected_class.return_value)))

    @patch('azure.mgmt.compute.ComputeManagementClient')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_credential_chain')
    def test_compute_client(self, mock_get_credential_chain, mock_compute_client):
        mock_credential_chain = mock_get_credential_chain.return_value

        util = AzureUtil('rg_name')
        compute_client = util.compute_client
        self.assertFalse(isinstance(compute_client, type(mock_compute_client.return_value)))

    @patch('azure.mgmt.network.NetworkManagementClient')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_credential_chain')
    def test_network_client(self, mock_get_credential_chain, mock_network_client):
        mock_credential_chain = mock_get_credential_chain.return_value
        util = AzureUtil('rg_name')
        network_client = util.network_client

    @patch('azure.mgmt.resource.ResourceManagementClient')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_credential_chain')
    def test_resource_client(self, mock_get_credential_chain, mock_resource_client):
        mock_credential_chain = mock_get_credential_chain.return_value
        util = AzureUtil('rg_name')
        resource_client = util.resource_client

    @patch('azure.mgmt.storage.StorageManagementClient')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_credential_chain')
    def test_storage_client(self, mock_get_credential_chain, mock_storage_client):
        mock_credential_chain = mock_get_credential_chain.return_value
        util = AzureUtil('rg_name')
        storage_client = util.storage_client

    @patch('azure.mgmt.authorization.AuthorizationManagementClient')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_credential_chain')
    def test_authorization_client(self, mock_get_credential_chain, mock_authorization_client):
        mock_credential_chain = mock_get_credential_chain.return_value
        util = AzureUtil('rg_name')
        result = util.authorization_client
        self.assertIsInstance(result, type(mock_authorization_client.return_value))

    @patch('azure.keyvault.secrets.SecretClient')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_credential_chain')
    def test_secret_client(self, mock_get_credential_chain, mock_secret_client):
        mock_credential_chain = mock_get_credential_chain.return_value
        mock_key_vault_url = 'https://your-key-vault-url/'
        util = AzureUtil('rg_name')
        secret_client = util.secret_client(mock_key_vault_url)

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.resource_client')
    def test_get_rg_name_list(self, mock_resource_client):
        mock_resource_groups = mock_resource_client.return_value.resource_groups
        util = AzureUtil('rg_name')
        rg_name_list = util.get_rg_name_list()

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_rg_name_list')
    @patch('apimrt.clouds.azure.azure_utils.logger')
    def test_update_resource_group_valid(self, mock_logger, mock_get_rg_name_list):
        mock_get_rg_name_list.return_value = ['rg1', 'rg2', 'rg3']
        util = AzureUtil('rg_name')
        util.update_resource_group('rg2')
        self.assertEqual(util.rg_name, 'rg2')
        mock_logger.assert_not_called()

        util.update_resource_group('invalid_rg')
        self.assertNotEqual(util.rg_name, 'rg_name')

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_get_vm_name_list(self, mock_compute_client):
        mock_vm_1 = MagicMock()
        mock_vm_1.name = 'vm1'
        mock_vm_2 = MagicMock()
        mock_vm_2.name = 'vm2'
        mock_vm_3 = MagicMock()
        mock_vm_3.name = 'vm3'
        mock_compute_client.return_value.virtual_machines.list.return_value = [
            mock_vm_1,
            mock_vm_2,
            mock_vm_3
        ]
        util = AzureUtil('rg_name')
        vm_name_list = util.get_vm_name_list()

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_get_scale_set_vm_name_list(self, mock_compute_client):
        mock_vmss_1 = MagicMock(name='VMSS1')
        mock_vmss_2 = MagicMock(name='VMSS2')
        mock_vmss_3 = MagicMock(name='VMSS3')
        mock_compute_client.return_value.virtual_machine_scale_set_vms.list.return_value = [
            mock_vmss_1,mock_vmss_2,mock_vmss_3
        ]
        util = AzureUtil('rg_name')
        scale_set_name = 'scale_set_name'
        vm_name_list = util.get_scale_set_vm_name_list(scale_set_name)
    
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_get_scale_set_name_list(self, mock_compute_client):
        mock_vmss_1 = MagicMock(name='VMSS1')
        mock_vmss_2 = MagicMock(name='VMSS2')
        mock_vmss_3 = MagicMock(name='VMSS3')
        mock_compute_client.return_value.virtual_machine_scale_sets.list.return_value = [
            mock_vmss_1,mock_vmss_2,mock_vmss_3]

        util = AzureUtil('rg_name')
        scale_set_name_list = util.get_scale_set_name_list()

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_get_scale_set_data(self, mock_compute_client):
        mock_scale_set = MagicMock(name='ScaleSet1')
        mock_compute_client.return_value.virtual_machine_scale_sets.get.return_value = mock_scale_set
        util = AzureUtil('rg_name')
        scale_set_name = 'scale_set_name'
        scale_set_data = util.get_scale_set_data(scale_set_name)

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_get_scale_set_vm_data(self, mock_compute_client):
        mock_vm_1 = MagicMock(name='VM1')
        mock_vm_2 = MagicMock(name='VM2')
        mock_vm_3 = MagicMock(name='VM3')
        mock_compute_client.return_value.virtual_machine_scale_set_vms.list.return_value = [
            mock_vm_1,mock_vm_2,mock_vm_3]
        util = AzureUtil('rg_name')
        scale_set_vm_data = util.get_scale_set_vm_data('scale_set_name')

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_vm_data')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.network_client')
    def test_get_scale_set_instance_ip_list(self, mock_network_client, mock_get_scale_set_vm_data):
        mock_scale_set_vm_1 = MagicMock()
        mock_scale_set_vm_1.network_profile_configuration.network_interface_configurations[0].name = 'nic1'
        mock_scale_set_vm_1.network_profile_configuration.network_interface_configurations[0].ip_configurations[0].name = 'ip_config1'
        mock_scale_set_vm_1.instance_id = 'instance_id1'

        mock_scale_set_vm_2 = MagicMock()
        mock_scale_set_vm_2.network_profile_configuration.network_interface_configurations[0].name = 'nic2'
        mock_scale_set_vm_2.network_profile_configuration.network_interface_configurations[0].ip_configurations[0].name = 'ip_config2'
        mock_scale_set_vm_2.instance_id = 'instance_id2'

        mock_get_scale_set_vm_data.return_value = [mock_scale_set_vm_1, mock_scale_set_vm_2]

        mock_network_interface = MagicMock()
        mock_network_interface.private_ip_address = '10.0.0.1'
        mock_network_client.network_interfaces.get_virtual_machine_scale_set_ip_configuration.return_value = mock_network_interface

        util = AzureUtil('rg_name')
        ip_list = util.get_scale_set_instance_ip_list('scale_set_name')

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_data')
    def test_get_scale_set_tags(self, mock_get_scale_set_data):
        mock_scale_set = MagicMock()
        mock_scale_set.tags = {'tag1': 'value1', 'tag2': 'value2'}
        mock_get_scale_set_data.return_value = mock_scale_set

        util = AzureUtil('rg_name')
        tags = util.get_scale_set_tags('scale_set_name')

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_tags')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_data')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.resource_client')
    def test_create_scale_set_tags(self, mock_get_scale_set_tags, mock_get_scale_set_data, mock_resource_client):
        mock_scale_set = MagicMock()
        mock_scale_set.id = 'scale_set_id'
        mock_get_scale_set_data.return_value = mock_scale_set
        mock_existing_tags = {'tag1': 'value1', 'tag2': 'value2', 'tag3': 'value3'}
        mock_get_scale_set_tags.return_value = mock_existing_tags

        util = AzureUtil('rg_name')
        tags = {'tag4': 'value4', 'tag5': 'value5'}
        util.create_scale_set_tags('scale_set_name', tags)

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_tags')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_data')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.resource_client')
    def test_delete_scale_set_tags(self, mock_create_or_update, mock_get_scale_set_data, mock_get_scale_set_tags):
        scale_set_name = 'test_scale_set'
        tags = {'tag1': 'value1','tag2': 'value2'}
        existing_tags = {'tag1': 'value1','tag2': 'value2','tag3': 'value3'}
        expected_updated_tags = {'tag3': 'value3'}

        mock_get_scale_set_tags.return_value = existing_tags
        mock_get_scale_set_data.return_value.id = 'test_scale_set_id'
        util = AzureUtil('rg_name')
        util.delete_scale_set_tags(scale_set_name, tags)

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.secret_client')
    def test_get_secret_value(self, mock_secret_client):
        azure_util = AzureUtil('rg_name')
        mock_client = MagicMock()
        mock_secret_client.return_value = mock_client
        mock_secret_client.return_value.get_secret.return_value.value = 'my_secret_value'
    
        result = azure_util.get_secret_value('secret_name', 'key_vault_url')
        self.assertEqual(result, 'my_secret_value')

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_get_instance_tags(self, mock_compute_client):
        azure_util = AzureUtil('rg_name')
        mock_vm = MagicMock()
        mock_vm.tags = {'tag1': 'value1', 'tag2': 'value2'}
        mock_compute_client_instance = mock_compute_client.return_value
        mock_compute_client_instance.virtual_machines.get.return_value = mock_vm
        tags = azure_util.get_instance_tags('instance_name')    

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_take_volume_snapshot(self, mock_compute_client):
        mock_vm = MagicMock()
        mock_vm.storage_profile.data_disks = [
            MagicMock(name='disk1', managed_disk=MagicMock(id='disk1_id')),
            MagicMock(name='disk2', managed_disk=MagicMock(id='disk2_id'))
        ]
        mock_compute_client.virtual_machines.get.return_value = mock_vm

        mock_snapshot = MagicMock()
        mock_snapshot.result.return_value = MagicMock(name='snapshot1')
        mock_compute_client.snapshots.begin_create_or_update.return_value = mock_snapshot
        
        azure_util = AzureUtil('rg_name')
        result = azure_util.take_volume_snapshot('vm1')

    def test_storage_connection_string(self):
        key_details = {
            "storage_account_name": "test_account",
            "key_value": "test_key"
        }
        util = AzureUtil('rg_name')
        util.get_storage_account_key = MagicMock(return_value=key_details)
        result = util.storage_connection_string()
        expected_result = f'DefaultEndpointsProtocol=https;AccountName={key_details["storage_account_name"]};AccountKey={key_details["key_value"]};EndpointSuffix=core.windows.net'
        self.assertEqual(result, expected_result)

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_name_list')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_tags')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_scale_set_data')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_update_image(self, mock_compute_client, mock_get_scale_set_data, mock_get_scale_set_tags, mock_get_scale_set_name_list):
        mock_scale_set_name_list = ['scale_set1', 'scale_set2']
        mock_get_scale_set_name_list.return_value = mock_scale_set_name_list
        mock_scale_set_tags = {'Subtype': 'message-processor'}
        mock_get_scale_set_tags.return_value = mock_scale_set_tags
        mock_scale_set_data = MagicMock()
        mock_get_scale_set_data.return_value = mock_scale_set_data
        mock_response = MagicMock()
        mock_response.result.return_value = True
        mock_compute_client.virtual_machine_scale_sets.begin_update.return_value = mock_response

        util = AzureUtil('rg_name')
        result = util.update_image('image_id')

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.network_client')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.compute_client')
    def test_get_instance_name_from_ip(self, mock_compute_client, mock_network_client):
        mock_nic1 = MagicMock()
        mock_nic1.ip_configurations = [
            MagicMock(private_ip_address='10.0.0.1'),
            MagicMock(private_ip_address='10.0.0.2')
        ]
        mock_nic1.virtual_machine.id = '/subscriptions/subscription_id/resourceGroups/rg_name/providers/Microsoft.Compute/virtualMachines/vm1'
        mock_nic2 = MagicMock()
        mock_nic2.ip_configurations = [
            MagicMock(private_ip_address='10.0.0.3'),
            MagicMock(private_ip_address='10.0.0.4')
        ]
        mock_nic2.virtual_machine.id = '/subscriptions/subscription_id/resourceGroups/rg_name/providers/Microsoft.Compute/virtualMachines/vm2'
        mock_network_client.network_interfaces.list.return_value = [mock_nic1, mock_nic2]
        mock_compute_client.virtual_machines.get.side_effect = lambda rg_name, vm_name: MagicMock(name=f"{rg_name}-{vm_name}")

        util = AzureUtil('rg_name')
        result = util.get_instance_name_from_ip('10.0.0.2', 'rg_name')

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.authorization_client')
    def test_get_instance_roles(self, mock_authorization_client):
        mock_role_assignment1 = MagicMock(role_definition_id='role1')
        mock_role_assignment2 = MagicMock(role_definition_id='role2')
        mock_role_assignment3 = MagicMock(role_definition_id='role3')

        mock_role_definition1 = MagicMock(role_name='Role1', permissions=[MagicMock(actions=['permission1'])])
        mock_role_definition2 = MagicMock(role_name='Role2', permissions=[MagicMock(actions=['permission2'])])
        mock_role_definition3 = MagicMock(role_name='Role3', permissions=[MagicMock(actions=['permission3'])])

        mock_authorization_client.role_assignments.list_for_resource.return_value = [
            mock_role_assignment1, mock_role_assignment2, mock_role_assignment3
        ]
        mock_authorization_client.role_definitions.get_by_id.side_effect = lambda role_id: {
            'role1': mock_role_definition1,
            'role2': mock_role_definition2,
            'role3': mock_role_definition3,
        }.get(role_id)

        util = AzureUtil('rg_name')
        result = util.get_instance_roles('vm1')

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_storage_account_name')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.storage_client')
    def test_get_storage_account_key(self, mock_storage_client, mock_get_storage_account_name):
        mock_storage_account_name = "storage_account_name"
        mock_get_storage_account_name.return_value = mock_storage_account_name

        mock_key = MagicMock()
        mock_key.value = "key_value"

        mock_storage_accounts = MagicMock()
        mock_storage_accounts.keys = [mock_key]
        mock_storage_client.storage_accounts.list_keys.return_value = mock_storage_accounts

        util = AzureUtil('rg_name')
        result = util.get_storage_account_key()

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_storage_account_list')
    def test_get_storage_account_name(self, mock_get_storage_account_list):
        mock_storage_account_list = [
            MagicMock(tags={"Subtype": "backup"}, name="backup_account"),
            MagicMock(tags={"Subtype": "other"}, name="other_account"),
        ]
        mock_get_storage_account_list.return_value = mock_storage_account_list
        util = AzureUtil('rg_name')
        result = util.get_storage_account_name()

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.storage_client')
    def test_get_storage_account_list(self, mock_storage_client):
        mock_storage_accounts = [
            MagicMock(name="storage_account1"),
            MagicMock(name="storage_account2"),
        ]
        mock_storage_client.storage_accounts.list_by_resource_group.return_value = mock_storage_accounts
        util = AzureUtil('rg_name')
        result = util.get_storage_account_list()

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.secret_client')
    def test_update_secrets(self, mock_secret_client):
        mock_secret_client_instance = MagicMock(name="secret_client_instance")
        mock_secret_client.return_value = mock_secret_client_instance
        util = AzureUtil('rg_name')
        result = util.update_secrets("secret_name", "secret_value", "key_vault_url")

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.secret_client')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.get_secret_value')
    def test_get_secrets(self, mock_secret_client, mock_secret_value):
        util = AzureUtil('rg_name')
        mock_secret_client_instance = MagicMock(name="secret_client_instance")
        mock_secret_client.return_value = mock_secret_client_instance
        mock_secret_properties = [
            MagicMock(name="secret_property1"),
            MagicMock(name="secret_property2")
        ]
        mock_secret_client_instance.list_properties_of_secrets.return_value = mock_secret_properties
        def mock_get_secret_value(key, kv_url):
            return f"Value for {key}"
        mock_get_secret_value.side_effect = mock_get_secret_value
        result = util.get_secrets("key_vault_url")

    @patch('azure.storage.blob.BlobServiceClient.from_connection_string')
    @patch('azure.storage.blob.BlobServiceClient.get_container_client')
    @patch('azure.storage.blob.BlobServiceClient.get_blob_client')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.storage_connection_string')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.download_from_blob')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.storage_client')
    def test_upload_to_blob_with_connection_string(self, mock_from_connection_string, mock_storage_connection_string, mock_download_from_blob, mock_container_client, mock_get_blob_client, mock_storage_client):
        container_name = 'test_container'
        blob_name = '/Users/I551770/Documents/GIT/new-upgrade/concourse_utils_apimrt/apimrt_utils/apimrt/clouds/azure/azure_utils.py'
        upload_file_path = '/Users/I551770/Documents/GIT/new-upgrade/concourse_utils_apimrt/apimrt_utils/apimrt/clouds/azure/azure_utils.py'
        mock_storage_connection_string.return_value = "default_connection_string"
        mock_from_connection_string.return_value = "from_connection_string"
        azure_util = AzureUtil('rg_name')
        azure_util.upload_to_blob(container_name, blob_name, upload_file_path)


    @patch('azure.storage.blob.BlobServiceClient.from_connection_string')
    @patch('azure.storage.blob.BlobServiceClient.get_container_client')
    @patch('azure.storage.blob.BlobServiceClient.get_blob_client')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.storage_connection_string')
    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.storage_client')
    def test_download_from_blob(self, mock_from_connection_string, mock_storage_connection_string, mock_container_client, mock_blob_client, mock_storage_client):
        blob_name = 'folder_name/file_name'
        download_file_path = '/path/to/your/file'
        mock_storage_connection_string.return_value = "default_connection_string"

        azure_util = AzureUtil('rg_name')
        azure_util.download_from_blob('test_container', blob_name, download_file_path)
    

    @patch('apimrt.clouds.azure.azure_utils.AzureUtil.secret_client')
    def test_update_secret_value(self, mock_secret_client, mock_client):
        azure_util = AzureUtil('rg_name')
        mock_secret_client.return_value = mock_client
        mock_secret_client.return_value.update_secret.return_value.value = 'my_secret_value'
        mock_client.update_secret = MagicMock()    
        result = azure_util.get_secret_value('secret_name', 'key_vault_url')
        updated_secrets = azure_util.update_secrets("new_key", "new_value", "test_secret")
        self.assertEqual(result, 'my_secret_value')