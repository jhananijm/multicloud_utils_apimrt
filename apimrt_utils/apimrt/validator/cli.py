"""Command-line interface for the APIM runtime validator.
"""

import json
from argparse import ArgumentParser, Namespace
from typing import Optional

from cliff.command import Command

from .types import ReportFile, RunList
from . import Validator
from .validation_lister import ValidationLister
from .validation.validate import ValidationClass
from os import path


class ValidatorCLI(Command):
    """Command-line interface for the APIM runtime validator

    Args:
        Command (Command): Registers the ValidatorCLI as a cliff `Command`.
    """

    def get_parser(self, prog_name: str) -> ArgumentParser:
        """Parses the command line arguments supplied to the validator command.

        Args:
            prog_name (str): The name of the program.

        Returns:
            ArgumentParser: The argument parser object.
        """

        parser = super().get_parser(prog_name)
        parser.add_argument(
            "-m",
            "--manifest",
            dest="manifest",
            help="The path to the validator manifest file",
            required=True,
        )
        parser.add_argument(
            "-r",
            "--report_file",
            dest="report_file",
            help="File to write the result report to",
        )
        parser.add_argument(
            "-f",
            "--report_format",
            dest="report_format",
            choices=[
                "csv",
                "html",
                "json",
                "latex",
            ],
            help="File format for the report file",
            default="html",
        )
        parser.add_argument(
            "-l",
            "--run",
            dest="run",
            help="Comma-separated list of tasks to run",
        )
        parser.add_argument(
            "-e",
            "--extra_vars",
            dest="extra_vars",
            help="Extra variables as a JSON string for Jinja2 templating",
            type=json.loads,
        )
        return parser

    def take_action(self, parsed_args: Namespace):
        """Runs the validation using the specified arguments.

        Args:
            parsed_args (Namespace): The parsed command-line arguments.
        """

        report_file: Optional[ReportFile] = None
        if parsed_args.report_file:
            report_file = (parsed_args.report_file, parsed_args.report_format)

        run: Optional[RunList] = None
        if parsed_args.run:
            run = parsed_args.run
            if run != "all":
                run = run.split(",")

        validator = Validator(
            parsed_args.manifest,
            extra_vars=parsed_args.extra_vars,
            report_file=report_file,
            run=run,
        )
        (stats, report) = validator.validate()
        print(report)
        if stats.has_failures():
            exit(1)


class ValidationListerCLI(Command):
    """Command-line interface for listing the validations

    Args:
        Command (Command): Registers the ValidatorCLI as a cliff `Command`.
    """

    def get_parser(self, prog_name: str) -> ArgumentParser:
        """Parses the command line arguments supplied to the validator command.

        Args:
            prog_name (str): The name of the program.

        Returns:
            ArgumentParser: The argument parser object.
        """

        parser = super().get_parser(prog_name)
        parser.add_argument(
            "-o",
            "--folder",
            dest="folder",
            help="The Path to Folder containing all validation yml.j2 files",
        )
        parser.add_argument(
            "-i",
            "--files",
            dest="files",
            help="Names of all the yml.j2 files as comma separated values(for common.yml.j2 and localhost.yml.j2-> common,localhost)",
            type=str,
        )
        parser.add_argument(
            "-r",
            "--report_file",
            dest="report_file",
            help="Path to write the result report",
        )
        parser.add_argument(
            "-f",
            "--report_format",
            dest="report_format",
            choices=[
                "table",
                "csv",
                "html",
                "json",
            ],
            help="File format for the report file",
            default="table",
        )
        return parser

    def take_action(self, parsed_args: Namespace):
        """Runs the validation using the specified arguments.

        Args:
            parsed_args (Namespace): The parsed command-line arguments.
        """

        folder = parsed_args.folder
        files = parsed_args.files
        if files is not None:
            files = files.split(',')
        report_file = parsed_args.report_file
        report_format = parsed_args.report_format

        validation_lister = ValidationLister(validation_folder=folder, validation_files=files)
        validation_lister.report(file_path=report_file, formatter=report_format)


class ValidationCLI(Command):
    """Command-line interface for listing the validations

    Args:
        Command (Command): Registers the ValidationCLI as a cliff `Command`.
    """

    def get_parser(self, prog_name: str) -> ArgumentParser:
        """Parses the command line arguments supplied to the validator command.

        Args:
            prog_name (str): The name of the program.

        Returns:
            ArgumentParser: The argument parser object.
        """
        VALIDATION_PATH = path.abspath(path.join(__file__, "../validations"))

        parser = super().get_parser(prog_name)
        parser.add_argument(
            "-i",
            "--inventory",
            dest="inventory",
            help="The Path to inventory file",
            required=True,
        )
        parser.add_argument(
            "-u",
            "--ms_url",
            dest="ms_url",
            help="MS URL",
            required=True,
        )
        parser.add_argument(
            "-a",
            "--admin_user",
            dest="admin_user",
            help="Admin User",
            required=True,
        )
        parser.add_argument(
            "-p",
            "--admin_password",
            dest="admin_password",
            help="Admin Password",
            required=True,
        )
        parser.add_argument(
            "-l",
            "--landscape_type",
            dest="landscape_type",
            help="Landscape Type",
            choices=[
                "dev",
                "prod",
            ],
            default="dev",
            required=True,
        )
        parser.add_argument(
            "-g",
            "--pg_password",
            dest="pg_password",
            help="PG Password",
            required=True,
        )
        parser.add_argument(
            "-d",
            "--ldap_password",
            dest="ldap_password",
            help="LDAP Password",
            type=str,
            required=True,
        )
        parser.add_argument(
            "-f",
            "--validations_folder",
            dest="validations_folder",
            help="Path to validation folder",
            type=str,
            required=False,
            default=VALIDATION_PATH,
        )


        parser.add_argument(
            "-c",
            "--components",
            help="Provide the components on which validation has to run by default will run on all the components in inv",
            type=str,
            required=False,
            default=None,

        )

        parser.add_argument(
            "-su",
            "--ssh_user",
            help="Provide the ssh user",
            type=str,
            required=False,
            default="concourseci",

        )

        parser.add_argument(
            "-sk",
            "--ssh_key",
            help="Provide the ssh private key",
            type=str,
            required=False,
            default="/etc/ansible/priv",

        )

        return parser

    def take_action(self, parsed_args: Namespace):
        """Runs the validation using the specified arguments.

        Args:
            parsed_args (Namespace): The parsed command-line arguments.
        """
        optional_components = None
        inv = parsed_args.inventory
        if parsed_args.components:
            optional_components = parsed_args.components.split(',')
        validations_folder = parsed_args.validations_folder
        extra_var = {
            "ansible_private_key": "/tmp/ssh-private-key",
            "ms_lb_ip": parsed_args.ms_url.replace('https://', ''),
            "admin_user": parsed_args.admin_user,
            "admin_password": parsed_args.admin_password,
            "pg_password": parsed_args.pg_password,
            "ldap_password": parsed_args.ldap_password,
            "landscape_type": parsed_args.landscape_type,
            "system_user" : parsed_args.ssh_user,
            "private_key" : parsed_args.ssh_key
        }

        validation = ValidationClass()

        validation.validate(extra_var=extra_var, validations_folder=validations_folder, inv_path=inv,optional_components=optional_components)
