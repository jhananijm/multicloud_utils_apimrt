import os
from pathlib import Path
import yaml
import json
import argparse
from prettytable import PrettyTable
from apimrt.apigee.cassandra.utils.cass_util import CassUtil
import sys

from apimrt.apigee.cassandra.utils.comm_util import DEFAULT_CONFIG_FILE_PATH, DEFAULT_OUTPUT_PATH


class MainCassandra:
    def __init__(self, cfg_path=None):
        if cfg_path is None:
            cfg_path = DEFAULT_CONFIG_FILE_PATH
        self.cfg_path = cfg_path
        self.fail_check = None

    def get_expected_compaction_config(self, cfg_path=None):
        with open(cfg_path, 'r') as compact_config:
            return yaml.safe_load(compact_config)

    def cassandra_prechecks(self, cass_ips, compaction_check_strategy, output_path=None):
        print(f"Cassandra list gen: {cass_ips}")
        data = self.get_expected_compaction_config(self.cfg_path)
        precheck_table = PrettyTable(['cassandra_node', 'compaction_check'])
        if output_path is None:
            output_path = DEFAULT_OUTPUT_PATH
        precheck_report_path = os.path.join(output_path, 'reports')
        # report output path
        Path(precheck_report_path).mkdir(parents=True, exist_ok=True)
        with open(os.path.join(precheck_report_path, "cassandra_precheck_report"), 'w') as cass_report_file:
            for ip in cass_ips:
                print(f"checking ip for the {ip}")
                cass = CassUtil(ip)
                compac_table_check = cass.get_compaction_table_check(data[compaction_check_strategy],
                                                                     compaction_check_strategy)
                print(compac_table_check)
                cass_report_file.write(str(compac_table_check))
                compac_list = json.loads(compac_table_check.get_json_string(header=False))
                compac_status = all(data['status'] for data in compac_list)
                if not compac_status:
                    precheck_table.add_row([ip, 'failed'])
                    self.fail_check = True
                else:
                    precheck_table.add_row([ip, 'passed'])
            cass_report_file.write(str(precheck_table))
        print(precheck_table)
        print(f"Detailed report is available in - {precheck_report_path}/cassandra_precheck_report")

        if self.fail_check:
            sys.exit(1)

    def cassandra_alter_command(self, ip, compaction_check_strategy, cmd_dir):
        data = self.get_expected_compaction_config(self.cfg_path)
        cass = CassUtil(ip)
        cass.cassandra_generate_alter_command(data[compaction_check_strategy], cmd_dir)

    def cassandra_rebuild_command(self, ip, compaction_check_strategy, cmd_dir):
        data = self.get_expected_compaction_config(self.cfg_path)
        cass = CassUtil(ip)
        cass.cassandra_generate_rebuild_command(data[compaction_check_strategy], cmd_dir)
