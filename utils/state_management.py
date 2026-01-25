import os
import json
import subprocess


class landscapestate:
    def __init__(self) -> None:
        pass

    def key_exists_in_state_file(self, key, path):
        with open(path, 'r') as file:
            data=json.loads(file.read())
        return key in data.keys()
        

    def run_command(self, command):
        command=command.split()
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Command Execution failed: {command}")
        else:
            return result.stdout.decode().strip()

    def fetch_key(self, key_list):
        landscape_type=self.run_command("iac get-config -i landscape -p landscape.type")
        landscape={"aws": 0, "azure": 1, "gcp": 2, "alibaba": 3}
        return key_list.split(",")[landscape[landscape_type]]
        

    def check_state_file_exists(self, file_path):
        return bool(os.path.exists(file_path) and os.path.isfile(file_path))
    
    def take_user_input(self, key, path):
        flag=True
        while flag:
            value=input(f"Set the value for {key} in state/{path.split('/state/')[1]}/state.json: ")
            print(f"Confirm the value set for {key} in state/{path.split('/state/')[1]}/state.json is {value}")
            conf=input("Enter [Y/y] to confirm: ")
            if conf in ["y", "Y"]:
                flag=False
        return value

    def write_to_state_file(self, data, path):
        with open(path, 'w') as file:
            file.write(data)

    def set_state_key(self, key, path):
        with open(path, 'r') as file:
            data=json.loads(file.read())
        value = self.take_user_input(key, path)
        data[key]=value
        self.write_to_state_file(json.dumps(data, indent=4), path)

    def set_state_file_and_key(self, key, path):
        value = self.take_user_input(key, path)
        data={key: value}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.write_to_state_file(json.dumps(data, indent=4), path)


def main():
    LANDSCAPE_ROOT_PATH = os.path.abspath("./../../../../../../")
    ls=landscapestate()
    #change the file location here 
    with open("./inputs/state_management_data.json", 'r') as file:
        input_data = json.loads(file.read())

    for k,path in input_data.items():
        key=ls.fetch_key(k)
        if ls.check_state_file_exists(f"{LANDSCAPE_ROOT_PATH}/{path}"):
            if not ls.key_exists_in_state_file(key, f"{LANDSCAPE_ROOT_PATH}/{path}"):
                ls.set_state_key(key,f"{LANDSCAPE_ROOT_PATH}/{path}")
        else:
            ls.set_state_file_and_key(key,f"{LANDSCAPE_ROOT_PATH}/{path}")
            




if __name__ == "__main__":
    main()