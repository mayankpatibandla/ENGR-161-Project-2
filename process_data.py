from csv import DictReader
from json import dump, load

data = {}


def foo(file):
    with open(f"data/{file}.csv", encoding='utf-8', newline='') as f:
        x = list(DictReader(f))
        power = x[0]
        efficiency = x[1]
        cost = x[2]

        result = {}
        for key in x[0].keys():
            result[key] = {
                "power": float(power[key]),
                "efficiency": float(efficiency[key]),
                "cost": float(cost[key]),
            }

        data[file] = result


def bar(file):
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


FOO_FILES = ["fermenters", "distillers", "filters"]
BAR_FILES = ["pumps", "pipes", "ductworks", "bends", "valves"]
JSON_FILE = "equipment"


def generate_json():
    for f in FOO_FILES:
        foo(f)
    for f in BAR_FILES:
        bar(f)

    with open(f"{JSON_FILE}.json", "w", encoding='utf-8') as f:
        dump(data, f, indent=2)


def load_json() -> dict[str, dict[str, dict[str, list[float] | float]]]:
    with open(f"{JSON_FILE}.json", "r", encoding='utf-8') as f:
        return load(f)
