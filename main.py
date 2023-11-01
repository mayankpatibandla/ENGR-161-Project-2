from argparse import ArgumentParser

from process_data import generate_json, load_json, print_raw

parser = ArgumentParser()
parser.add_argument("--json", dest="generate_json", help="Generates a JSON file", action="store_true")
parser.add_argument("--raw", dest="print_raw", help="Prints the raw data", action="store_true")
parser.add_argument("--print", dest="print_data", help="Prints the JSON data", action="store_true")
args = parser.parse_args()

data = load_json()

if args.generate_json:
    generate_json()

if args.print_raw:
    print_raw()

if args.print_data:
    print(data)
