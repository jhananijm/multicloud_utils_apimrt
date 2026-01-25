import sys
from typing import Any, Optional
from time import time
import json
import base64
import logging

from google.auth import compute_engine
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import secretmanager
from google.cloud import compute_v1

logger = logging.getLogger(__name__)

class GcpUtil:
    def __init__(self, project_id=None):
        self.project_id = project_id
    
    def wait_for_extended_operation(self, operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 1200) -> Any:
        result = operation.result(timeout=timeout)
        
        if operation.error_code:
            logger.error(
                f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}")
            logger.error(f"Operation ID: {operation.name}")
            raise operation.exception() or RuntimeError(operation.error_message)

        if operation.warnings:
            logger.info(f"Warnings during {verbose_name}:\n")
            for warning in operation.warnings:
                logger.info(f" - {warning.code}: {warning.message}")

        return result
    
    def get_instance_data(self, ip_address, project_name):
        instance_client = compute_v1.InstancesClient()
        request = compute_v1.AggregatedListInstancesRequest()
        request.project = self.project_id
        request.max_results = 50
        agg_list = instance_client.aggregated_list(request=request)
        for zone, response in agg_list:
            instances = response.instances
            for instance in instances:
                if instance.metadata and instance.network_interfaces:
                    ins_metadata = instance.metadata.items
                    ins_network = instance.network_interfaces
                    meta_flag = any(metadata.key == "project" and project_name in metadata.value for metadata in ins_metadata)
                    ip_flag = any(network_interface.network_i_p == ip_address for network_interface in ins_network)
                    if ip_flag and meta_flag:
                        return instance, zone
        return None, None
    
    def get_instance_name(self, ip_address, project_name):
        instance_data, zone = self.get_instance_data(ip_address, project_name)
        if instance_data is not None:
            return instance_data.name
        logger.info(f"No Instance found with the following IP: {ip_address} in Project: {project_name}")
        return None
    
    def get_instance_tags(self, ip_address, project_name):
        tags = {}
        instance_data, zone = self.get_instance_data(ip_address, project_name)
        if instance_data is not None:
            ins_metadata = instance_data.metadata.items
            for metadata in ins_metadata:
                tags[metadata.key] = metadata.value
            return tags
                               
    def get_secrets(self, secret_id: str):
        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": secret_name})
        secret_value = response.payload.data.decode("UTF-8")
        return json.loads(secret_value)  
    
    def update_secrets(self, key: str, value: str, secret_id: str):
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{self.project_id}/secrets/{secret_id}"
            secret = client.get_secret(request={"name": secret_name})
            versions = client.list_secret_versions(request={"parent": secret_name})
            latest_version = ""
            for version in versions:
                if version.state == secretmanager.SecretVersion.State.ENABLED:
                    latest_version = version.name.split('/')[-1]
                    break
            version_name = f"{secret_name}/versions/{latest_version}"
            response = client.access_secret_version(request={"name": version_name})
            payload_data = response.payload.data.decode("UTF-8")
            payload_dict = json.loads(payload_data)
            payload_dict[key] = value
            updated_payload_data = json.dumps(payload_dict)
            updated_payload_data_bytes = updated_payload_data.encode("UTF-8")
            new_version = client.add_secret_version(
                request={"parent": secret_name, "payload": {"data": updated_payload_data_bytes}}
            )
            return self.get_secrets(secret_id)
            #print(f"Secret value updated successfully! New version: {new_version.name}")
        except Exception as excp:
            logger.error(f"UpdateFailedError: {excp}")
            raise excp
        
    
    def list_attached_volumes(self, zone, instance_name):
        compute_client = compute_v1.InstancesClient()
        response = compute_client.get(project=self.project_id, zone=zone, instance=instance_name)
        attached_volumes = []
            
        for disk in response.disks:
            if disk.source and not disk.boot:
                volume_name = disk.source.split('/')[-1]
                attached_volumes.append(volume_name)

        return attached_volumes
    
    def create_volume_snapshot(
        self,
        project_id: str,
        disk_name: str,
        snapshot_name: str,
        *,
        zone: Optional[str] = None,
        region: Optional[str] = None,
        location: Optional[str] = None,
        disk_project_id: Optional[str] = None,
        ) -> compute_v1.Snapshot:
        """
        Create a snapshot of a disk.
        You need to pass `zone` or `region` parameter relevant to the disk you want to
        snapshot, but not both. Pass `zone` parameter for zonal disks and `region` for
        regional disks.
        Args:
            project_id: project ID or project number of the Cloud project you want
                to use to store the snapshot.
            disk_name: name of the disk you want to snapshot.
            snapshot_name: name of the snapshot to be created.
            zone: name of the zone in which is the disk you want to snapshot (for zonal disks).
            region: name of the region in which is the disk you want to snapshot (for regional disks).
            location: The Cloud Storage multi-region or the Cloud Storage region where you
                want to store your snapshot.
                You can specify only one storage location. Available locations:
                https://cloud.google.com/storage/docs/locations#available-locations
            disk_project_id: project ID or project number of the Cloud project that
                hosts the disk you want to snapshot. If not provided, will look for
                the disk in the `project_id` project.
        Returns:
            The new snapshot instance.
        """
        if zone is None and region is None:
            raise RuntimeError(
                "You need to specify `zone` or `region` for this function to work."
            )
        if zone is not None and region is not None:
            raise RuntimeError("You can't set both `zone` and `region` parameters.")

        if disk_project_id is None:
            disk_project_id = project_id

        if zone is not None:
            disk_client = compute_v1.DisksClient()
            disk = disk_client.get(project=disk_project_id, zone=zone, disk=disk_name)
        else:
            regio_disk_client = compute_v1.RegionDisksClient()
            disk = regio_disk_client.get(
                project=disk_project_id, region=region, disk=disk_name
            )

        snapshot = compute_v1.Snapshot()
        snapshot.source_disk = disk.self_link
        snapshot.name = snapshot_name
        if location:
            snapshot.storage_locations = [location]

        snapshot_client = compute_v1.SnapshotsClient()
        operation = snapshot_client.insert(project=project_id, snapshot_resource=snapshot)

        self.wait_for_extended_operation(operation, "Snapshot Creation")

        return snapshot_client.get(project=project_id, snapshot=snapshot_name)
    
    
    def take_volume_snapshot(self, instance_ip, project_name):
        instance_data, zone = self.get_instance_data(instance_ip, project_name)
        snapshots = []
        if instance_data is not None:
            instance_name = instance_data.name
            zone = (zone.split("/"))[1]
            volumes = self.list_attached_volumes(zone, instance_name)
            for volume in volumes:
                snapshot_name = f"{volume}-{int(time())}"
                resp = self.create_volume_snapshot(project_id=self.project_id, disk_name=volume, snapshot_name=snapshot_name, zone=zone)
                snapshots.append(resp.name)
            return snapshots
                