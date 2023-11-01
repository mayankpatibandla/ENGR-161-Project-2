from csv import DictReader
from json import dump

data = {}


def foo(file):
    with open(f"data/{file}.csv", encoding='utf-8', newline='') as f:
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
    with open(f"data/{file}.csv", encoding='utf-8', newline='') as f:
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
    with open(f"data/{file}.csv", encoding='utf-8', newline='') as f:
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
    with open(f"data/{file}.csv", encoding='utf-8', newline='') as f:
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
