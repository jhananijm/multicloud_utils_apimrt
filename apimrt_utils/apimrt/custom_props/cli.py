from argparse import ArgumentParser, Namespace

import pathlib
from cliff.command import Command
from pathlib import Path

from . import CustomProps


__DEFAULT_CIPHERS_CONF__: Path = pathlib.Path(__file__).parent / "config/tls12_cbc_deprecate.yml"


class CustomPropsCLI(Command):
    """Command-line interface for the customer properties modifier.

    Args:
        Command (Command): Registers the CustomPropsCLI as a cliff `Command`.
    """

    def get_parser(self, prog_name: str) -> ArgumentParser:
        """Parses the command-line arguments supplied to the custom props modify command.

        Args:
            prog_name (str): The name of the program.

        Returns:
            ArgumentParser: The argument parser object.
        """

        parser = super(CustomPropsCLI, self).get_parser(prog_name)
        parser.add_argument(
            "-p",
            "--props_file",
            dest="props_file",
            help="Path to the .properties file",
            required=True,
        )
        parser.add_argument(
            "-c",
            "--conf_file",
            dest="conf_file",
            help="Path to the configuration YAML file",
            default=str(__DEFAULT_CIPHERS_CONF__),
        )

        return parser

    def take_action(self, parsed_args: Namespace):
        """Modifies the properties file using the configuration file.

        Args:
            parsed_args (Namespace): The parsed command-line arguments.
        """

        try:
            custom_props = CustomProps(
                parsed_args.props_file,
                parsed_args.conf_file,
            )
            custom_props.modify()

        except Exception as _e:
            print(_e)
