from pathlib import Path
import yaml
import os
import jinja2
from prettytable import PrettyTable, ALL

DEFAULT_VALIDATION_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "validations"))
DEFAULT_VALIDATION_FILES = ['localhost', 'common', 'ldap', 'ms', 'pg', 'qpid', 'zkcs']
DEFAULT_OUTPUT_PATH = "/tmp"


class ValidationLister:
    def __init__(self, validation_folder=None, validation_files=None):
        if validation_folder is None:
            validation_folder = DEFAULT_VALIDATION_FOLDER
        self.validation_folder = validation_folder
        if validation_files is None:
            validation_files = DEFAULT_VALIDATION_FILES
        self.validation_files = validation_files

    def __formatter(self, table, formatter=None):
        """
        :param table:
        :param formatter:
        :return:
        """
        if formatter == 'table':
            return table
        elif formatter == 'json':
            return table.get_json_string(header=False)
        elif formatter == 'csv':
            return table.get_csv_string()
        elif formatter == 'html':
            return table.get_html_string()

    def get_data(self, file_name):
        validation_file = os.path.abspath(os.path.join(self.validation_folder, f"{file_name}.yml.j2"))
        with open(validation_file, 'r') as file:
            template_content = file.read()

        # Render the Jinja template
        template = jinja2.Template(template_content)
        rendered_content = template.render()

        # Load the rendered YAML content as a dictionary
        data = yaml.safe_load(rendered_content)

        # Remove the 'run' and 'server_group' section
        data.pop('run')
        data.pop('server_groups')

        return data

    def validations(self, formatter):
        table = PrettyTable(["Validation Name", "Task Name", "Description", "Command"])
        table.align['Command'] = "l"
        table.hrules = ALL
        table.horizontal_char = '-'

        for files in self.validation_files:
            data = self.get_data(files)
            name = data['name']
            tasks = data['tasks']
            for task in tasks:
                task_name = task['name']
                description = task['description']
                for val in task['validations']:
                    key_val = list(val.keys())[0]
                    if key_val == "remoteshell":
                        command = val['remoteshell']['command']
                    elif key_val == "apicall":
                        command = val['apicall']
                    else:
                        command = ""

                    table.add_row([name, task_name, description, command])

        return self.__formatter(table, formatter)

    def report(self, file_path=None, formatter="table"):
        if file_path is None:
            file_path = DEFAULT_OUTPUT_PATH
        Path(file_path).mkdir(parents=True, exist_ok=True)
        formatted_data = self.validations(formatter)
        if formatter == "table":
            formatted_data = formatted_data.get_string()
        print(formatted_data)
        with open(os.path.join(file_path, "validation_list.txt"), "w") as file:
            file.write(formatted_data)
        print(f"validation_list.txt exported to {file_path}")
