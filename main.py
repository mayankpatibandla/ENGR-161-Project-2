from argparse import ArgumentParser
from csv import DictReader
from json import dump

# pipe_diameter = 0.1 # meters
# num_pipe_bends = int(input("Number of pipe bends: "))
# pipe_length_before_fermenter = float(input("Pipe length before fermenter (feet): "))
# pipe_length_after_distiller = float(input("Pipe length after distiller (feet): "))

# fermenter_efficiency = float(input("Fermenter efficiency: "))
# distiller_efficiency = float(input("Distiller efficiency: "))
# filter_efficiency = float(input("Filter efficiency: "))
# dehydrator_efficiency = float(input("Dehydrator efficiency: "))
# pump_efficiency = float(input("Pump efficiency: "))

# num_valves = int(input("Number of valves: "))
# valve_loss_coefficient = 800

# total_target = 100000 # gallons per day of "pure" ethanol

# fluid_velocity_into_distiller = 3.6 # m/s
# kinetic_energy_waste_fermenter = 9.7e4 # J/day
# mass_sugar_leaving_system = 8.2e3 # kg/day

parser = ArgumentParser()
parser.add_argument("--json", dest="generate_json", help="Generates a json file", action="store_true")
parser.add_argument("--print", dest="print_data", help="Prints the data", action="store_true")
args = parser.parse_args()

data = {}


def foo(file):
    with open(f"{file}.csv", encoding='utf-8', newline='') as f:
        x = list(DictReader(f))
        power = x[0]
        efficiency = x[1]
        cost = x[2]

        print(f"{file.title()}:")
        for key in x[0].keys():
            print(f"  {key}:")
            print(f"    {power[key]}", "kWh/day")
            print(f"    {efficiency[key]}")
            print(f"    {cost[key]}", "$ per m^3 / hour of flow")
        print("\n")


def foo2(file):
    with open(f"{file}.csv", encoding='utf-8', newline='') as f:
        x = list(DictReader(f))
        power = x[0]
        efficiency = x[1]
        cost = x[2]

        result = {}
        for key in x[0].keys():
            result[key] = {
                "power": int(power[key]),
                "efficiency": float(efficiency[key]),
                "cost": int(cost[key]),
            }

        data[file] = result


def bar(file):
    with open(f"{file}.csv", encoding='utf-8', newline='') as f:
        x = list(DictReader(f))
        coefficient = x[0]
        costs = x[1:]

        print(f"{file.title()}:")
        for key in x[0].keys():
            print(f"  {key}:")
            if key.find("(m)") != -1:
                for cost in costs:
                    print(f"    {cost[key]}", "meters")
                continue
            print(f"    {coefficient[key]}")
            for cost in costs:
                print(f"    {cost[key]}", "$ per ...")
        print("\n")


def bar2(file):
    with open(f"{file}.csv", encoding='utf-8', newline='') as f:
        x = list(DictReader(f))
        coefficient = x[0]
        costs = x[1:]

        result = {}
        for key in x[0].keys():
            result[key] = {}
            if key.find("(m)") != -1:
                result[key] = [float(cost[key]) for cost in costs]
                continue
            if coefficient[key] != '':
                result[key]["coefficient"] = float(coefficient[key])
            result[key]["cost"] = [float(cost[key]) for cost in costs]

        data[file] = result


foo_files = ["fermenters", "distillers", "filters"]
bar_files = ["pumps", "pipes", "ductworks", "bends", "valves"]


def generate_json():
    for f in foo_files:
        foo2(f)
    for f in bar_files:
        bar2(f)

    with open("equipment.json", "w", encoding='utf-8') as f:
        dump(data, f, indent=2)


def print_data():
    for f in foo_files:
        foo(f)
    for f in bar_files:
        bar(f)


if args.generate_json:
    generate_json()

if args.print_data:
    print_data()
