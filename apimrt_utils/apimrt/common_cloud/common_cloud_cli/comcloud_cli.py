from cliff.command import Command
from cliff.lister import Lister
from apimrt.common_cloud.utils.commcloud_utils import get_cloud_obj
import json
import logging


class GetProjectName(Command):
    """Provides the cloud project name"""

    def get_parser(self, prog_name):
        parser = super(GetProjectName, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        cloud = get_cloud_obj()
        print(cloud.get_project_name())


class GetProjectSecretName(Command):
    """Provides the cloud project secret name"""

    def get_parser(self, prog_name):
        parser = super(GetProjectSecretName, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        cloud = get_cloud_obj()
        print(cloud.get_project_secret_name())


class UpdateSecrets(Command):
    """Updates the secrets by default updates the project secrets"""

    def get_parser(self, prog_name):
        parser = super(UpdateSecrets, self).get_parser(prog_name)
        parser.add_argument("--secret_name", type=str, required=False,
                            help="provide the secret id or secret name by default uses the project secret",
                            default=None)
        parser.add_argument("--key", type=str, required=True,
                            help="provide key to be updated",
                            )
        parser.add_argument("--value", type=str, required=True,
                            help="provide value to be updated",
                            )
        return parser

    def take_action(self, parsed_args):
        secret_name = parsed_args.secret_name
        key = parsed_args.key
        value = parsed_args.value

        cloud = get_cloud_obj()
        print(json.dumps(cloud.update_secrets(key, value, secret_name=secret_name), indent=4))


class GetCloudType(Command):
    """Provides the cloud type"""

    def get_parser(self, prog_name):
        parser = super(GetCloudType, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        cloud = get_cloud_obj()
        print(cloud.name)


class GetSecret(Command):
    """Provides the cloud secrets"""

    def get_parser(self, prog_name):
        parser = super(GetSecret, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        cloud = get_cloud_obj()
        print(json.dumps(cloud.get_secrets(), indent=4))


class GetScalingGroups(Command):
    """Provides the scaling groups"""

    def get_parser(self, prog_name):
        parser = super(GetScalingGroups, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        cloud = get_cloud_obj()
        print(json.dumps(cloud.get_scaling_groups(), indent=4))


class GetAvailablePermissions(Command):
    """Provides the available permissions of the instance"""

    def get_parser(self, prog_name):
        parser = super(GetAvailablePermissions, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        cloud = get_cloud_obj()
        print(json.dumps(cloud.get_available_permissions(), indent=4))


class GetRequiredPermissions(Command):
    """Required permissions for the instance to orchestrate workflows"""

    def get_parser(self, prog_name):
        parser = super(GetRequiredPermissions, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        cloud = get_cloud_obj()
        print(json.dumps(cloud.get_required_permissions(), indent=4))


class PerformPermissionCheck(Command):
    """Perform permission check provides the list of required permissions to be attached to the instance"""

    def get_parser(self, prog_name):
        parser = super(PerformPermissionCheck, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        cloud = get_cloud_obj()
        print(json.dumps(cloud.get_missing_permissions(), indent=4))


class GetInstanceNameFromIPAndProjectName(Command):
    """Fetches instance name from given private ip and project name"""

    def get_parser(self, prog_name):
        parser = super(GetInstanceNameFromIPAndProjectName, self).get_parser(prog_name)
        parser.add_argument("--private_ip", type=str, required=True,
                            help="Provide private ip of the instance")
        parser.add_argument("--project_name", type=str, required=True,
                            help="Provide project name of the instance")
        return parser

    def take_action(self, parsed_args):
        private_ip = parsed_args.private_ip
        project_name = parsed_args.project_name
        cloud = get_cloud_obj()
        print(cloud.get_instance_name(private_ip, project_name))


class GetInstanceNameFromIP(Command):
    """Fetches instance name from given private ip"""

    def get_parser(self, prog_name):
        parser = super(GetInstanceNameFromIP, self).get_parser(prog_name)
        parser.add_argument("--private_ip", type=str, required=True,
                            help="Provide private ip of the instance")
        return parser

    def take_action(self, parsed_args):
        private_ip = parsed_args.private_ip
        cloud = get_cloud_obj()
        print(cloud.get_project_instance_name(private_ip))


class GetInstanceTags(Command):
    """Gets Instance tags from given instance ip"""

    def get_parser(self, prog_name):
        parser = super(GetInstanceTags, self).get_parser(prog_name)
        parser.add_argument("--private_ip", type=str, required=True,
                            help="Provide private ip of the instance")
        return parser

    def take_action(self, parsed_args):
        private_ip = parsed_args.private_ip
        cloud = get_cloud_obj()
        print(cloud.get_instance_tags(private_ip))


class TakeVolumeSnapshot(Command):
    """Takes snapshot of volumes attached to an instance from given instance ip"""

    def get_parser(self, prog_name):
        parser = super(TakeVolumeSnapshot, self).get_parser(prog_name)
        parser.add_argument("--private_ip", type=str, required=True,
                            help="Provide private ip of the instance")
        return parser

    def take_action(self, parsed_args):
        private_ip = parsed_args.private_ip
        cloud = get_cloud_obj()
        print(cloud.take_volume_snapshot(private_ip))


class UpdateImage(Command):
    """Updates the image of all MP and Router ASG in a landscape with given image id"""

    def get_parser(self, prog_name):
        parser = super(UpdateImage, self).get_parser(prog_name)
        parser.add_argument("--image_id", type=str, required=True,
                            help="Provide image id to update")
        return parser

    def take_action(self, parsed_args):
        image_id = parsed_args.image_id
        cloud = get_cloud_obj()
        print(cloud.update_image(image_id))
