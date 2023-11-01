from csv import DictReader

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

def foo(file):
    with open(f"{file}.csv", newline='') as f:
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

def bar(file):
    with open(f"{file}.csv", newline='') as f:
        x = list(DictReader(f))
        efficiency = x[0]
        cost = x[1]

        print(f"{file.title()}:")
        for key in x[0].keys():
            print(f"  {key}:")
            print(f"    {efficiency[key]}")
            print(f"    {cost[key]}", "$ per m^3 / hour of flow")
        print("\n")

foo_files = ["fermenters", "distillers", "filters"]
bar_files = ["pumps"]

for f in foo_files:
    foo(f)

for f in bar_files:
    bar(f)