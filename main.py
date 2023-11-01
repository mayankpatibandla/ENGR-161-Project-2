from argparse import ArgumentParser

from process_data import generate_json, print_data

parser = ArgumentParser()
parser.add_argument("--json", dest="generate_json", help="Generates a json file", action="store_true")
parser.add_argument("--print", dest="print_data", help="Prints the data", action="store_true")
args = parser.parse_args()

if args.generate_json:
    generate_json()

if args.print_data:
    print_data()
