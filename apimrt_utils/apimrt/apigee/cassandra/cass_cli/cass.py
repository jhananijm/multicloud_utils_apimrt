from cliff.command import Command
from apimrt.apigee.cassandra.utils.cass_methods import MainCassandra
from apimrt.apigee.cassandra.utils.comm_util import DEFAULT_CONFIG_FILE_PATH, get_available_compac_checks, \
    DEFAULT_CMD_GEN_DIR, DEFAULT_OUTPUT_PATH

COMPACT_STRATEGY_TYPES = get_available_compac_checks()


class CompactionValidation(Command):
    """Validates the compaction strategy across cass cluster"""

    def get_parser(self, prog_name):
        parser = super(CompactionValidation, self).get_parser(prog_name)
        parser.add_argument("--cass_ips", type=str, required=True,
                            help="Provide cassandra ips as comma seperated values")
        parser.add_argument("--compac_strategy", nargs='?', default="column_family_compaction_strategy", type=str,
                            help=f"Suppored Compaction stategy checks {COMPACT_STRATEGY_TYPES}")
        parser.add_argument("--cfg_file", nargs='?', default=DEFAULT_CONFIG_FILE_PATH, type=str,
                            help="Provide path to config file")
        parser.add_argument("--output_dir", nargs='?', default=f"{DEFAULT_OUTPUT_PATH}", type=str,
                            help=f"Path to precheck report directory, default in {DEFAULT_OUTPUT_PATH}/reports")
        return parser

    def take_action(self, parsed_args):
        cass_ips = parsed_args.cass_ips
        compact_strategy = parsed_args.compac_strategy
        cfg_file = parsed_args.cfg_file
        output_path = parsed_args.output_dir
        cass = MainCassandra(cfg_file)
        cass.cassandra_prechecks(cass_ips.split(','), compact_strategy, output_path)


class AlterCmdGenerator(Command):
    """Generates Alter commands"""

    def get_parser(self, prog_name):
        parser = super(AlterCmdGenerator, self).get_parser(prog_name)
        parser.add_argument("--cass_ips", type=str, required=True,
                            help="Provide cassandra ips as comma separated values")
        parser.add_argument("--compac_strategy", nargs='?', default="column_family_compaction_strategy", type=str,
                            help=f"Suppored Compaction stategy checks {COMPACT_STRATEGY_TYPES}")
        parser.add_argument("--cfg_file", nargs='?', default=DEFAULT_CONFIG_FILE_PATH, type=str,
                            help="Provide path to config file")
        parser.add_argument("--cmd_dir", nargs='?', default=f"{DEFAULT_CMD_GEN_DIR}", type=str,
                            help=f"Path to commands file will be available default in {DEFAULT_CMD_GEN_DIR}/alter")
        return parser

    def take_action(self, parsed_args):
        cass_ips = parsed_args.cass_ips
        compact_strategy = parsed_args.compac_strategy
        cfg_file = parsed_args.cfg_file
        cmd_dir = parsed_args.cmd_dir
        cass = MainCassandra(cfg_file)
        cass.cassandra_alter_command(cass_ips.split(',')[0], compact_strategy, cmd_dir)


class RebuildCmdGenerator(Command):
    """Generates Rebuild commands"""

    def get_parser(self, prog_name):
        parser = super(RebuildCmdGenerator, self).get_parser(prog_name)
        parser.add_argument("--cass_ips", type=str, required=True,
                            help="Provide cassandra ips as comma separated values")
        parser.add_argument("--compac_strategy", nargs='?', default="column_family_compaction_strategy", type=str,
                            help=f"Suppored Compaction stategy checks {COMPACT_STRATEGY_TYPES}")
        parser.add_argument("--cfg_file", nargs='?', default=DEFAULT_CONFIG_FILE_PATH, type=str,
                            help="Provide path to config file")
        parser.add_argument("--cmd_dir", nargs='?', default=f"{DEFAULT_CMD_GEN_DIR}", type=str,
                            help=f"Path to commands file will be available default in {DEFAULT_CMD_GEN_DIR}/rebuild")
        return parser

    def take_action(self, parsed_args):
        cass_ips = parsed_args.cass_ips
        compact_strategy = parsed_args.compac_strategy
        cfg_file = parsed_args.cfg_file
        cmd_dir = parsed_args.cmd_dir
        cass = MainCassandra(cfg_file)
        cass.cassandra_rebuild_command(cass_ips.split(',')[0], compact_strategy, cmd_dir)
