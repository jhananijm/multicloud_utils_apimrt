import yaml
import json
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from prettytable import PrettyTable
import sys
import os
from pathlib import Path
from apimrt.apigee.cassandra.utils.comm_util import DEFAULT_CMD_GEN_DIR
import logging
from shutil import rmtree

logging.getLogger('cassandra.cluster').setLevel(logging.WARNING)

parent_path = os.path.dirname(os.path.abspath(__file__))


class CassUtil:
    KEYSPACES_COMPACTION = "SELECT * from system.schema_columnfamilies"
    REBUILD_INDEX = "SELECT keyspace_name, columnfamily_name, index_name from system.schema_columns"
    DC_INFO = "SELECT data_center FROM system.local"
    RACK_INFO = "SELECT rack FROM system.local"

    def __init__(self, cassandra_ip='127.0.0.1', port=9042):
        '''

        :param cassandra_ip:
        :param port:
        '''
        self.cassandra_ip = cassandra_ip
        self.port = port

    def __cass_stmt_execution(self, stmt):
        '''

        :param stmt:
        :return:
        '''
        cluster = Cluster([self.cassandra_ip], self.port, load_balancing_policy=RoundRobinPolicy(), protocol_version=3)
        session = cluster.connect()
        data = session.execute(stmt)
        session.shutdown()
        return data

    def __formatter(self, table, formatter=None):
        '''

        :param table:
        :param format:
        :return:
        '''
        if formatter is None:
            return table
        elif formatter == 'json':
            return table.get_json_string(header=False)
        elif formatter == 'csv':
            return table.get_csv_string()
        elif formatter == 'html':
            return table.get_html_string()
        elif formatter == 'dict':
            return json.loads(table.get_json_string(header=False))

    def get_keyspaces(self):
        '''
        Return the keyspaces of cassandra cluster
        :return:
        '''
        data = self.__cass_stmt_execution(CassUtil.KEYSPACES_COMPACTION)
        keyspace_data = list(set([keyspace_data.keyspace_name for keyspace_data in data]))
        return keyspace_data

    def __get_compaction_strategy_keyspaces(self):
        '''

        :return:
        '''
        data = self.__cass_stmt_execution(CassUtil.KEYSPACES_COMPACTION)
        return [[self.cassandra_ip, keyspace_data.keyspace_name, keyspace_data.columnfamily_name,
                 keyspace_data.compaction_strategy_class.split('.')[-1]] for keyspace_data in data]

    def get_compaction_strategy(self, keyspace_filter=None, formatter=None):
        '''
         Return the compaction strategy of all keyspaces and column family by default
         provide key space filter as list to return compaction strategy of selected keyspaces
         default format is table (csv,json,html,dict) are supported

        :param keyspace_filter:
        :param formatter:
        :return:
        '''

        if keyspace_filter is None:
            keyspace_filter = []
        compaction_list = self.__get_compaction_strategy_keyspaces()
        table = PrettyTable(['cassandra_ip', 'keyspace_name', 'columnfamily_name', 'compaction_strategy'])
        if len(keyspace_filter) != 0:
            [table.add_row(items) for items in compaction_list if items[1] in keyspace_filter]
        else:
            [table.add_row(items) for items in compaction_list]
        return self.__formatter(table, formatter)

    def validate_compaction_strategy(self, keyspace_dict, formatter=None):

        '''

         Return the validated compaction strategy as a table
         default formatter is table (csv,json,html,dict) are supported

        :param keyspace_dict: example {"kms":"LeveledCompactionStrategy"}
        :return:
        '''

        compaction_list = self.__get_compaction_strategy_keyspaces()
        table = PrettyTable(
            ['cassandra_ip', 'keyspace_name', 'columnfamily_name', 'compaction_strategy', 'expected_compaction',
             'status'])
        for items in compaction_list:
            if items[1] in keyspace_dict.keys():
                items.append(keyspace_dict[items[1]])
                if keyspace_dict[items[1]] == items[3]:
                    items.append(True)
                else:
                    items.append(False)
                table.add_row(items)
        return self.__formatter(table, formatter)

    def keyspace_column_family_concatenation(self, data, flag):
        concatenated_list = []
        if flag == 'present':
            for item in data:
                keyspace_column_family = f"{item[1]}~{item[2]}"
                concat_item = [item[0], keyspace_column_family, item[3]]
                concatenated_list.append(concat_item)
        if flag == 'expected':
            for keyspace, column_dict in data.items():
                for column_family, compaction_strategy in column_dict.items():
                    kes_col_fam = f"{keyspace}~{column_family}"
                    concat_item = [kes_col_fam, compaction_strategy]
                    concatenated_list.append(concat_item)
        return concatenated_list

    def validate_column_family_compaction_strategy(self, keyspace_dict, format=None):
        '''

        :param keyspace_dict:
        :return:
        '''

        expected_compaction_strategy = self.keyspace_column_family_concatenation(keyspace_dict, flag='expected')
        compaction_list = self.__get_compaction_strategy_keyspaces()
        concatenated_compaction_list = self.keyspace_column_family_concatenation(compaction_list, flag='present')

        table = PrettyTable(
            ['cassandra_ip', 'keyspace_name', 'columnfamily_name', 'compaction_strategy', 'expected_compaction',
             'status'])
        for present in concatenated_compaction_list:
            for expected in expected_compaction_strategy:
                if present[1] == expected[0]:
                    expected_compaction = expected[1]
                    status = expected_compaction == present[2]
                    row = [present[0], present[1].split('~')[0], present[1].split('~')[1], present[2],
                           expected_compaction, status]
                    table.add_row(row)
        return self.__formatter(table, format)

    def get_compaction_table_check(self, keyspace_dict, compaction_check_strategy):
        if compaction_check_strategy == "column_family_compaction_strategy":
            return self.validate_column_family_compaction_strategy(keyspace_dict)
        elif compaction_check_strategy == "compaction_strategy":
            return self.validate_compaction_strategy(keyspace_dict)
        else:
            print("Invalid key for Compaction Strategy check")
            sys.exit(1)

    def cassandra_generate_alter_command(self, data, cmd_dir=None):
        # creating folder if it doesn't exist
        if cmd_dir is None:
            cmd_dir = DEFAULT_CMD_GEN_DIR
        cmd_dir_path = os.path.join(cmd_dir, 'alter')
        Path(cmd_dir_path).mkdir(parents=True, exist_ok=True)
        for keyspace, column_family in data.items():
            with open(os.path.join(cmd_dir_path, f"{keyspace}_alter.sh"), 'w') as alter_file:
                alter_file.write(
                    '''#!/bin/bash\n# Alter tables analytics\n/opt/apigee/apigee-cassandra/bin/cqlsh `hostname -i` -e "\n''')
                for column_family_name, compact_strategy in column_family.items():
                    alter_file.write(
                        f"ALTER TABLE {keyspace}.{column_family_name} WITH compaction = {{'class' : '{compact_strategy}'}};")
                alter_file.write('''"\n''')
        print(f"The alter files are available in {cmd_dir_path}")

    def get_rebuild_indexes(self):
        '''

        :return:
        '''
        data = self.__cass_stmt_execution(CassUtil.REBUILD_INDEX)
        return [[rebuild_index.keyspace_name, rebuild_index.columnfamily_name,
                 rebuild_index.index_name] for rebuild_index in data]

    def cassandra_generate_rebuild_command(self, data, cmd_dir=None):
        if cmd_dir is None:
            cmd_dir = DEFAULT_CMD_GEN_DIR
        cmd_dir_path = os.path.join(cmd_dir, 'rebuild')
        if os.path.exists(cmd_dir_path):
            rmtree(cmd_dir_path)
        Path(cmd_dir_path).mkdir(parents=True, exist_ok=True)
        # creating folder if it doesn't exist
        rebuild_indexes = self.get_rebuild_indexes()
        for keyspace in data.keys():
            for item in rebuild_indexes:
                if keyspace == item[0] and item[2] is not None:
                    with open(os.path.join(cmd_dir_path, f"{keyspace}_rebuild.sh"), 'a') as rebuild_file:
                        rebuild_file.write(
                            f"/opt/apigee/apigee-cassandra/bin/nodetool rebuild_index {item[0]} {item[1]} {item[2]}\n")

        print(f"The rebuild files are available in {cmd_dir_path}")

    def get_dc(self):
        data = self.__cass_stmt_execution(CassUtil.DC_INFO)
        row = data.one()
        return row.data_center

    def get_rack(self):
        data = self.__cass_stmt_execution(CassUtil.RACK_INFO)
        row = data.one()
        return row.rack

    def get_dc_number(self):
        dc = self.get_dc()
        dc_number = dc.split('-')[1]
        return dc_number

    def get_rack_number(self):
        rack = self.get_rack()
        rack_number = rack.split('-')[1]
        return rack_number
