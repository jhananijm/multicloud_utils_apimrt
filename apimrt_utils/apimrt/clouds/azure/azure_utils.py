import logging
import os
import subprocess
import json
import re
import datetime
from datetime import timezone
from itertools import tee
from subprocess import CalledProcessError
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ChainedTokenCredential, \
    AzureCliCredential, ManagedIdentityCredential, EnvironmentCredential
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import HttpResponseError
from azure.mgmt.compute.models import VirtualMachineScaleSetStorageProfile, \
    VirtualMachineScaleSet, VirtualMachineScaleSetVMProfile, ImageReference
from azure.mgmt.compute.models import Snapshot

logger = logging.getLogger(__name__)

class AzureUtil:
    def __init__(self, rg_name: str, subscription_id: str = None) -> str:
        '''
        :param rg_name: Resource group name
        :param subscription_id: Subscription id
        '''
        self.rg_name = rg_name
        self.subscription_id = subscription_id
        #
        if self.subscription_id is None:
            self.subscription_id = os.environ.get(
                'AZURE_SUBSCRIPTION_ID', None)
        #
        try:
            if self.subscription_id is None:
                output = subprocess.check_output('az account show', shell=True)
                data = json.loads(output)
                self.subscription_id = data['id']
        except CalledProcessError as excp:
            logger.error(excp)
        #
        try:
            if self.subscription_id is None:
                output = subprocess.check_output(
                    'az login --identity', shell=True)
                data = json.loads(output)
                self.subscription_id = data[0]['id']
        except CalledProcessError as excp:
            logger.error(excp)

    def get_credential_chain(self):
        mgmt_cred = ManagedIdentityCredential()
        cli_cred = AzureCliCredential()
        env_cred = EnvironmentCredential()
        default_cred = DefaultAzureCredential()
        return ChainedTokenCredential(mgmt_cred, cli_cred, env_cred, default_cred)

    @property
    def compute_client(self):
        return ComputeManagementClient(
            credential=self.get_credential_chain(),
            subscription_id=self.subscription_id
            )

    @property
    def network_client(self):
        return NetworkManagementClient(
            credential=self.get_credential_chain(),
            subscription_id=self.subscription_id
            )

    @property
    def resource_client(self):
        return ResourceManagementClient(
            credential=self.get_credential_chain(),
            subscription_id=self.subscription_id
            )

    @property
    def storage_client(self):
        return StorageManagementClient(
            credential=self.get_credential_chain(),
            subscription_id=self.subscription_id
            )
    @property
    def authorization_client(self):
        return AuthorizationManagementClient(
            credential=self.get_credential_chain(),
            subscription_id=self.subscription_id
        )

    def secret_client(self, key_vault_url: str):
        return SecretClient(
            credential=self.get_credential_chain(),
            vault_url=key_vault_url
            )

    def get_rg_name_list(self):
        return [rg.name for rg in self.resource_client.resource_groups.list()]

    def update_resource_group(self, rg_name):
        if rg_name in self.get_rg_name_list():
            self.rg_name = rg_name
        else:
            logger.error('Not a valid Resource group name')

    def get_vm_name_list(self):
        return [vm.name for vm in \
                self.compute_client.virtual_machines.list(
                    resource_group_name=self.rg_name
                )]

    def get_vm_name_from_ip(self,vm_ip):
        vm_list = self.get_vm_name_list()
        for vm in vm_list:
            nic = vm.network_profile.network_interfaces[0].id
            nic = nic.split("/")[-1]
            network_interface = self.compute_client.network_interfaces.get(self.rg_name, nic)
            for ipconfig in network_interface.ip_configurations:
                if ipconfig.private_ip_address == vm_ip:
                    print(vm.name)

    def get_scale_set_vm_name_list(self, scale_set_name: str):
        return [vmss.name for vmss in
                self.compute_client.virtual_machine_scale_set_vms.list(
                    resource_group_name=self.rg_name,
                    virtual_machine_scale_set_name=scale_set_name
                )]

    def get_scale_set_name_list(self):
        return [vmss.name for vmss in
                self.compute_client.virtual_machine_scale_sets.list(
                    resource_group_name=self.rg_name
                )]

    def get_scale_set_data(self, scale_set_name: str):
        return self.compute_client.virtual_machine_scale_sets.get(
            resource_group_name=self.rg_name,
            vm_scale_set_name=scale_set_name
            )

    def get_scale_set_vm_data(self, scale_set_name: str):
        return self.compute_client.virtual_machine_scale_set_vms.list(
            resource_group_name=self.rg_name,
            virtual_machine_scale_set_name=scale_set_name
            )

    def get_scale_set_instance_ip_list(self, scale_set_name: str):
        ip_list = []
        scale_set_list = self.get_scale_set_vm_data(scale_set_name)
        for scale_set in scale_set_list:
            nic_name = scale_set.network_profile_configuration.network_interface_configurations[
                0].name
            ip_config = scale_set.network_profile_configuration.network_interface_configurations[
                0].ip_configurations[0].name
            instance_id = scale_set.instance_id
            ip_address = self.network_client.network_interfaces.get_virtual_machine_scale_set_ip_configuration(
                self.rg_name, scale_set_name, instance_id, nic_name, ip_config).private_ip_address
            logger.info(
                f'NIC name: {nic_name}, IP config: {ip_config}, Instance_ID: {instance_id}, IP address: {ip_address}')
            ip_list.append(ip_address)
        return ip_list

    def get_scale_set_tags(self, scale_set_name: str):
        return self.get_scale_set_data(scale_set_name).tags

    def create_scale_set_tags(self, scale_set_name: str, tags: dict):
        all_tags = self.get_scale_set_tags(scale_set_name=scale_set_name)
        logger.info(f'Existing tags: {all_tags}, Tags to be updated: {tags}')
        for tag in tags:
            all_tags[tag] = tags[tag]
        tag_body = {
            "operation": "create",
            "properties": {
                "tags": all_tags
            }
        }
        resource_id = self.get_scale_set_data(scale_set_name).id
        logger.info(f'Resource ID: {resource_id}, Tags: {all_tags}')
        self.resource_client.tags.create_or_update_at_scope(
            resource_id, tag_body)

    def delete_scale_set_tags(self, scale_set_name: str, tags: dict):
        all_tags = self.get_scale_set_tags(scale_set_name=scale_set_name)
        logger.info(f'Existing tags: {all_tags}, Tags to be deleted: {tags}')
        for tag in tags:
            if tag in all_tags:
                del all_tags[tag]
        tag_body = {
            "operation": "create",
            "properties": {
                "tags": all_tags
            }
        }
        resource_id = self.get_scale_set_data(scale_set_name).id
        logger.info(f'Resource ID: {resource_id}, Tags: {all_tags}')
        self.resource_client.tags.create_or_update_at_scope(
            resource_id, tag_body)

    def upload_to_blob(self, container_name: str, blob_name: str, upload_file_path: str, connection_string: str = None):
        # Example: download_from_blob(container_name='test_container', blob_name='folder_name/file_name', upload_file_path='/home/file_name', connection_string)
        if connection_string is None:
            logger.info('Connection string not provided, using default')
            connection_string = self.storage_connection_string()
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string)

        container_list = blob_service_client.list_containers()
        if container_name not in [container.name for container in container_list]:
            blob_service_client.create_container(container_name)
        else:
            logger.info(f'Container {container_name} already exists')

        container_client = blob_service_client.get_container_client(
            container_name)
        blob_list = [blob.name for blob in container_client.list_blobs()]
        logger.info(
            f'Uploading {upload_file_path} to {container_name}/{blob_name}')
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name)

        if blob_name in blob_list:
            time_stamp = datetime.datetime.now(
                datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f%Z")
            logger.info(
                f'Blob {blob_name} already exists backing up contents to {blob_name}_backup_{time_stamp}')
            backup = blob_service_client.get_blob_client(
                container=container_name, blob=f'{blob_name}_backup_{time_stamp}')
            file_contents = self.download_from_blob(
                container_name=container_name, blob_name=blob_name)
            backup.upload_blob(file_contents, overwrite=True)

        with open(upload_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

    def download_from_blob(self, container_name: str, blob_name: str, download_file_path: str = None, connection_string: str = None):
        # Example: download_from_blob(container_name='test_container', blob_name='folder_name/file_name', download_file_path='/home/file_name', connection_string)
        if connection_string is None:
            logger.info('Connection string not provided, using default')
            connection_string = self.storage_connection_string()
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string)
        container_list = blob_service_client.list_containers()
        if container_name not in [container.name for container in container_list]:
            logger.error(f'Container {container_name} not found')
            return
        container_client = blob_service_client.get_container_client(
            container_name)
        blob_list = [blob.name for blob in container_client.list_blobs()]
        if blob_name not in blob_list:
            logger.error(f'Blob {blob_name} not found')
            return
        if download_file_path is None:
            logger.info(
                f'Downloading {container_name}/{blob_name} content to object')
            blob_client = blob_service_client.get_blob_client(
                container=container_name, blob=blob_name)
            return blob_client.download_blob().readall()
        else:
            logger.info(
                f'Downloading {container_name}/{blob_name} to {download_file_path}')
            with open(download_file_path, "wb") as data:
                blob_client = blob_service_client.get_blob_client(
                    container=container_name, blob=blob_name)
                blob_data = blob_client.download_blob()
                blob_data.readinto(data)

    def get_secrets(self, key_vault_url: str):
        # To be optimized
        secrets = {}
        try:
            secret_properties = self.secret_client(
                key_vault_url).list_properties_of_secrets()
            key_list = [keys.__dict__['_vault_id'].__dict__[
                '_resource_id'].__dict__['name'] for keys in secret_properties]
            for key in key_list:
                secrets[key] = self.get_secret_value(key, key_vault_url)
            return secrets
        except ResourceNotFoundError as excp:
            logger.error(excp)
            # return None
            raise excp

    def get_secret_value(self, secret_name: str, key_vault_url: str):
        try:
            return self.secret_client(key_vault_url).get_secret(secret_name).value
        except ResourceNotFoundError as excp:
            logger.error(excp)
            # return None
            raise excp

    def update_secrets(self, secret_name: str, secret_value: str, key_vault_url: str):
        try:
            self.secret_client(key_vault_url).set_secret(
                secret_name, secret_value)
            return self.get_secrets(key_vault_url)
        except ResourceNotFoundError as excp:
            logger.error(excp)
            raise excp

    def get_storage_account_list(self):
        return list(
            self.storage_client.storage_accounts.list_by_resource_group(
                self.rg_name
            )
        )

    def get_storage_account_name(self):
        storage_account_list = self.get_storage_account_list()
        for storage_account in storage_account_list:
            if storage_account.tags['Subtype'] == 'backup':
                return storage_account.name

    def get_storage_account_key(self):
        storage_account_name = self.get_storage_account_name()
        return {"storage_account_name": storage_account_name, "key_value": [key.value for key in self.storage_client.storage_accounts.list_keys(self.rg_name, storage_account_name).keys][0]}

    def storage_connection_string(self):
        key_details = self.get_storage_account_key()
        return f'DefaultEndpointsProtocol=https;AccountName={key_details["storage_account_name"]};AccountKey={key_details["key_value"]};EndpointSuffix=core.windows.net'

    def get_image_rg_scaleset(self, scale_set_name):
        scale_set_vms = self.compute_client.virtual_machine_scale_sets.get(
            resource_group_name = self.rg_name,
            vm_scale_set_name = scale_set_name,
        )
        image_reference = scale_set_vms.virtual_machine_profile.storage_profile.image_reference.id
        pattern = r"resourceGroups/([^/]+)"
        match = re.search(pattern, image_reference)
        if match:
            image_rg = match.group(1)
        return image_rg
    
    def update_image(self, scale_set_name, image_rg, image_id):
        try:
            scale_set_data = self.get_scale_set_data(scale_set_name)
            image_name = f"/subscriptions/{self.subscription_id}/resourceGroups/{image_rg}/providers/Microsoft.Compute/images/{image_id}"
                        
            vm_profile = VirtualMachineScaleSetVMProfile(
                storage_profile=VirtualMachineScaleSetStorageProfile(image_reference=ImageReference(id=image_name)))
                    
            parameters = VirtualMachineScaleSet(location=scale_set_data.location,virtual_machine_profile=vm_profile)

            response = self.compute_client.virtual_machine_scale_sets.begin_update(
                resource_group_name=self.rg_name,vm_scale_set_name=scale_set_name,parameters=parameters)
            if response.result():
                return scale_set_name
            
        except HttpResponseError as excep:
            logger.error(excep)
            raise excep

    def take_volume_snapshot(self,vm_name):
        try:
            vm = self.compute_client.virtual_machines.get(self.rg_name, vm_name)
            snapshot_name_suffix = datetime.datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
            snapshot_names = []
            for data_disk in vm.storage_profile.data_disks:
                snapshot = self.compute_client.snapshots.begin_create_or_update(
                    self.rg_name,
                    f"{data_disk.name}-{snapshot_name_suffix}",
                    {
                        "location": vm.location,
                        "creation_data": {
                            "create_option": "Copy",
                            "source_uri": data_disk.managed_disk.id,
                        },
                    },
                )
                snapshot.wait()
                snapshot_name = snapshot.result().name
                snapshot_names.append(snapshot_name)
            return snapshot_names

        except ResourceNotFoundError as excep:
            logger.error(excep)
            raise excep

    def get_instance_roles(self, vm_name):
        response = self.authorization_client.role_assignments.list_for_resource(
            resource_group_name=self.rg_name,
            resource_provider_namespace="Microsoft.Compute",
            resource_type="virtualMachines",
            resource_name=vm_name,
        )
        role_map = {}
        for item in response:
            role_definition = self.authorization_client.role_definitions.get_by_id(role_id=item.role_definition_id)
            role_name = role_definition.role_name
            permissions = []
            for itr in role_definition.permissions:
                permissions = itr.actions
            role_map.update({role_name:permissions})
        print(role_map)
        _list = []
        for name,permission in role_map.items():
            for itr in permission:
                _list.append(itr)
        print(_list)
            
    def get_instance_name_from_ip(self, instance_ip, rg_name):
        nic = self.network_client.network_interfaces.list(rg_name)
        for n in nic:
            for ip in n.ip_configurations:
                if ip.private_ip_address == instance_ip:
                    vm_name = n.virtual_machine.id.split('/')[-1]
                    return self.compute_client.virtual_machines.get(rg_name, vm_name).name
                else:
                    instance_name = self.get_vmss_instance_name_from_ip(instance_ip, rg_name)
                    if instance_name:
                        return instance_name
    
    def get_vmss_instance_name_from_ip(self, instance_ip, rg_name):
        scale_set_list = self.get_scale_set_name_list()
        for scale_set in scale_set_list:
            scale_set_data = self.get_scale_set_vm_data(scale_set)
            for scale_data in scale_set_data:
                nic_name = scale_data.network_profile_configuration.network_interface_configurations[0].name
                ip_config = scale_data.network_profile_configuration.network_interface_configurations[
                            0].ip_configurations[0].name
                instance_id = scale_data.instance_id
                ip_address = self.network_client.network_interfaces.get_virtual_machine_scale_set_ip_configuration(
                rg_name, scale_set, instance_id, nic_name, ip_config).private_ip_address
                if ip_address == instance_ip:
                    return scale_data.name

    def get_instance_tags(self, instance_name):
        vm = self.compute_client.virtual_machines.get(self.rg_name, instance_name)
        return vm.tags