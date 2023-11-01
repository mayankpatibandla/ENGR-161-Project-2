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


def main():
    for fermenter_name, fermenter_data in data["fermenters"].items():
        for distiller_name, distiller_data in data["distillers"].items():
            for filter_name, filter_data in data["filters"].items():
                for pump_name, pump_data in data["pumps"].items():
                    if pump_name.find('(m)') != -1:
                        continue
                    for pipe_name, pipe_data in data["pipes"].items():
                        if pipe_name.find('(m)') != -1:
                            continue
                        for ductwork_name, ductwork_data in data["ductworks"].items():
                            if ductwork_name.find('(m)') != -1:
                                continue
                            for bend_angle, bend_data in data["bends"].items():
                                if bend_angle.find('(m)') != -1:
                                    continue
                                for valve_name, valve_data in data["valves"].items():
                                    if valve_name.find('(m)') != -1:
                                        continue


if __name__ == '__main__':
    main()
