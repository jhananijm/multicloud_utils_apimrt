from apimrt.common_cloud.utils.commcloud_utils import get_cloud_obj
import argparse
import json
import yaml
from os import path


def arg_parse():
    # Initialize parser
    parser = argparse.ArgumentParser()

    # Adding optional argument
    parser.add_argument(
        "-o",
        "--output_file",
        dest="output_file",
        help="Output Path for the secrets",
        required=True,
    )

    # Read arguments from command line
    return parser.parse_args()

def alter_secrets(data):
    input_file = path.abspath(path.join(__file__,'..', 'config/secrets_key_mapping.yml'))
    with open(input_file, 'r') as file:
        alter_data = yaml.safe_load(file)
        for k,v in alter_data.items():
            for i in v:
                if i in data.keys():
                    temp = data[i]
                    del data[i]
                    data[k] = temp
    return data
    

def main():
    arg = arg_parse()
    cloud_obj = get_cloud_obj()
    data = cloud_obj.get_secrets()

    data = alter_secrets(data)

    with open(arg.output_file, 'w') as file:
        json.dump(data, file)



if __name__ == "__main__":
    main()
