import json
from argparse import ArgumentParser, Namespace
from typing import Dict

from cliff.command import Command

from apimrt.common_cloud.utils.commcloud_utils import get_cloud_obj
from . import SilentConfig


class SilentConfigCLI(Command):
    """Command-line interface for the silent config generator.

    Args:
        Command (Command): Registers the SilentConfigCLI as a cliff `Command`.
    """

    def get_parser(self, prog_name: str) -> ArgumentParser:
        """Parses the command-line arguments supplied to the silent config command.

        Args:
            prog_name (str): The name of the program.

        Returns:
            ArgumentParser: The argument parser object.
        """

        parser = super(SilentConfigCLI, self).get_parser(prog_name)
        parser.add_argument(
            "-i",
            "--inventory",
            dest="inventory",
            help="Path to the Ansible inventory file",
            required=True,
        )
        parser.add_argument(
            "-s",
            "--secrets_file",
            dest="secrets_file",
            help="Path to the file containing secrets",
            default=None,
        )
        parser.add_argument(
            "-e",
            "--extra_vars",
            dest="extra_vars",
            help="Extra variables as a JSON string for Jinja2 templating",
            type=json.loads,
            default="{}",
        )
        parser.add_argument(
            "-o",
            "--output_dir",
            dest="output_dir",
            help="Output directory for generated config files",
            default=".",
        )
        parser.add_argument(
            "-u",
            "--ssh_user",
            dest="ssh_user",
            help="SSH username for uploading config files",
            default="concourseci",
        )
        parser.add_argument(
            "-k",
            "--ssh_private_key",
            dest="ssh_private_key",
            help="SSH private key file path for uploading config files",
            default="/etc/ansible/priv",
        )
        parser.add_argument(
            "-p",
            "--ssh_port",
            dest="ssh_port",
            help="SSH port for uploading config files",
            default=22,
        )
        parser.add_argument(
            "--no_upload",
            dest="no_upload",
            help="Don't upload config files to nodes",
            default=False,
        )
        return parser

    def take_action(self, parsed_args: Namespace):
        """Generates the silent config file using the specified arguments.

        Args:
            parsed_args (Namespace): The parsed command-line arguments.
        """

        extra_vars: Dict[str, str] = parsed_args.extra_vars
        secrets: Dict[str, str] = {}

        try:
            if parsed_args.secrets_file:
                with open(parsed_args.secrets_file, "r") as _f:
                    secrets = json.load(_f)
            else:
                cloud = get_cloud_obj()
                secrets = cloud.get_secrets()

            extra_vars["admin_email"] = secrets["msusername"]
            extra_vars["admin_password"] = secrets["mspassword"]
            extra_vars["ldap_password"] = secrets["ldappassword"]
            extra_vars["pg_password"] = secrets["pgpassword"]

            silent_config = SilentConfig(
                parsed_args.inventory,
                extra_vars=extra_vars,
                output_dir=parsed_args.output_dir,
                ssh_user=parsed_args.ssh_user,
                ssh_private_key=parsed_args.ssh_private_key,
                ssh_port=parsed_args.ssh_port,
            )
            silent_config.render()

            if not parsed_args.no_upload:
                silent_config.upload()
        except Exception as _e:
            print(_e)
