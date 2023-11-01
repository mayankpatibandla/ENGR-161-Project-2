from argparse import ArgumentParser

from process_data import generate_json, load_json

parser = ArgumentParser()
parser.add_argument("--json", dest="generate_json", help="Generates a JSON file", action="store_true")
parser.add_argument("--print", dest="print_data", help="Prints the JSON data", action="store_true")
args = parser.parse_args()


if args.generate_json:
    generate_json()

data = load_json()

if args.print_data:
    print(data)
