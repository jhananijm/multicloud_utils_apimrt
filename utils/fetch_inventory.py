import copy
import argparse
import json

def arg_parser():
    # Initialize parser
    parser = argparse.ArgumentParser()

    # Adding optional argument
    parser.add_argument("-p", "--path", required=True, default=".")
    parser.add_argument("-i", "--inv", required=True)
    parser.add_argument("-c", "--component", required=False, default=None)

    # Return arguments from command line
    return parser.parse_args()

def inv_to_dict(args):
    # inv to dict code block
    value = []
    flag = 0
    inv = {}

    with open(args.inv, 'r') as file:
        data = file.read()

    for d in data.split("\n"):
        if "[" in d:
            if flag != 0:
                inv[key] = copy.deepcopy(value)
                value.clear()
            key = d.replace("[", "").replace("]", "")
            flag = 1
        else:
            if d != '':
                value.append(d)
    inv[key] = value
    return inv

def write_inventory_to_context(inventory, args):
    with open(f'{args.path}/inventory.json', 'w') as file:
        file.write(json.dumps(inventory))

def write_component_inventory_to_context(args, inv):
    for comp,value in inv.items():
        with open(f'{args.path}/{comp}_inventory', 'w') as file:
            file.write("\n".join(value))

def main():
    args = arg_parser()
    inv = inv_to_dict(args)
    write_inventory_to_context(inv, args)
    write_component_inventory_to_context(args, inv)    

if __name__ == "__main__":
    main()