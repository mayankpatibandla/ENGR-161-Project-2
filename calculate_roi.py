import json
import csv

import matplotlib
from matplotlib import pyplot as plt

with open("2.json", encoding="utf-8") as f:
    data = json.load(f)

kWh_per_cubic_meter_ethanol = 5877.83

x_values = []
y_values = []
capital = []
fermenters = []
filters = []
distillers = []
dehydrators = []

mass_CO2 = 0

with open("equipment.json", encoding="utf-8") as f:
    equipment = json.load(f)
    for value in data.values():
        energy_output = kWh_per_cubic_meter_ethanol * value["Q Out"]

        total_kWh_per_day_input = (
            equipment["fermenters"][value["Fermenter"]]["power"]
            + equipment["filters"][value["Filter"]]["power"]
            + equipment["distillers"][value["Distiller"]]["power"]
            + equipment["filters"][value["Dehydrator"]]["power"]
            + value["Pump Energy"]
        )

        x_values.append(total_kWh_per_day_input)
        y_values.append(energy_output)
        capital.append(value["Cost"])
        fermenters.append(value["Fermenter"])
        filters.append(value["Filter"])
        distillers.append(value["Distiller"])
        dehydrators.append(value["Dehydrator"])

        mass_CO2 = value["Mass CO2"]

roi = []
for i in range(len(x_values)):
    roi.append(y_values[i] / x_values[i])

# z = []
# for i in range(len(roi)):
#     z.append(roi[i] / capital[i])

max_val = max(roi)
max_index = roi.index(max_val)
max_roi = roi[max_index]
max_capital = capital[max_index]
max_fermenter = fermenters[max_index]
max_filter = filters[max_index]
max_distiller = distillers[max_index]
max_dehydrator = dehydrators[max_index]

# print(
#     f"Max ratio: {max_val}, Max ROI: {max_roi}, Max Capital: {max_capital}, Max Fermenter: {max_fermenter}, Max Filter: {max_filter}, Max Distiller: {max_distiller}, Max Dehydrator: {max_dehydrator}"
# )

def print_best():
    print(
        f"Max ROI: {max_roi}, Input: {x_values[max_index]} kWh/day, Output: {y_values[max_index]} kWh/day, Capital: {max_capital}, Best Fermenter: {max_fermenter}, Best Filter: {max_filter}, Best Distiller: {max_distiller}, Best Dehydrator: {max_dehydrator}, Best Pump: Premium, Best Pipe: Glorious, Best Valve: Glorious, Diameter: 0.15m".replace(", ", "\n")
    )

def create_plot():
    # plt.style.use("dark_background")
    # ax = plt.axes(projection="3d", label="Capital")

    plt.scatter(x_values, y_values)
    plt.scatter(x_values[max_index], y_values[max_index], color="red")

    plt.xlabel("kWh per day input")
    plt.ylabel("kWh per day output")
    # plt.zlabel("Capital Cost")
    plt.title("ROI")

    plt.ticklabel_format(style='sci', axis='both', scilimits=(0, 0))

    # print(matplotlib.style.available)

    plt.show()

def roi_to_csv():
    with open("roi.csv", "w", encoding="utf-8") as f:
        csv.writer(f).writerows(zip(x_values, y_values))
