from os import path
import yaml
from pathlib import Path

ROOT_PATH = path.abspath(path.join(__file__, "../.."))
DEFAULT_CONFIG_FILE_PATH = path.abspath(path.join(__file__, f"{ROOT_PATH}/config/compaction_strategy.yml"))
DEFAULT_CMD_GEN_DIR = "/tmp/casstools"
DEFAULT_OUTPUT_PATH = "/tmp/cass_validation/outputs"


def get_available_compac_checks():
    with open(DEFAULT_CONFIG_FILE_PATH, 'r') as config_file:
        compact_strategy_types = list(yaml.safe_load(config_file))
    return compact_strategy_types
