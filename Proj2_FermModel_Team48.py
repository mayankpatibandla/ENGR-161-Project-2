# File: Proj2_FermModel_Team48.py
# Date: 11/05/2023
# By: Mayank Patibandla
# mpatiban
# Joshua Buss
# buss12
# Alexander Molotiu
# amolotiu
# Michael Lee
# lee4557
# Section: 3
# Team: 48
#
# ELECTRONIC SIGNATURE
# Mayank Patibandla
# Joshua Buss
# Alexander Molotiu
# Michael Lee
#
# The electronic signatures above indicate that the program
# submitted for evaluation is the combined effort of all
# team members and that each member of the team was an
# equal participant in its creation. In addition, each
# member of the team has a general understanding of
# all aspects of the program development and execution.
#
# This program determines the optimal equipment configuration for an ethanol
# production plant.The program takes in a volumetric flow rate and outputs the
# optimal equipment configuration based on the highest return on investment.

from argparse import ArgumentParser
from csv import DictReader, writer
from json import dump, dumps, load
from math import cbrt, pi
from textwrap import dedent

from matplotlib import pyplot as plt

# Parge arguments
parser = ArgumentParser()
parser.add_argument(
    "--json",
    dest="generate_json",
    help="Generates a JSON file",
    action="store_true",
)
parser.add_argument(
    "--print",
    dest="print_data",
    help="Prints the JSON data",
    action="store_true",
)
parser.add_argument(
    "--generate",
    dest="generate_configs",
    help="Generates 1.json and flow.json",
    action="store_true",
)
parser.add_argument(
    "--roi",
    dest="calculate_roi",
    help="Calculates the roi",
    action="store_true",
)
parser.add_argument(
    "--plot", dest="create_plot", help="Creates a plot", action="store_true"
)
args = parser.parse_args()


JSON_FILE = "equipment.json"


def generate_json() -> None:
    """
    Generates a JSON file for equipment from the individual CSV files
    """
    equipment_data = {}

    for file in ["fermenters", "distillers", "filters"]:
        with open(f"{file}.csv", encoding="utf-8", newline="") as f:
            x = list(DictReader(f))
            power = x[0]
            efficiency = x[1]
            cost = x[2]

            result = {}
            for key in x[0].keys():
                # Convert to float
                result[key] = {
                    "power": float(power[key]),
                    "efficiency": float(efficiency[key]),
                    "cost": float(cost[key]),
                }
            equipment_data[file] = result
    for file in ["pumps", "pipes", "ductworks", "bends", "valves"]:
        with open(f"{file}.csv", encoding="utf-8", newline="") as f:
            x = list(DictReader(f))
            coefficient = x[0]
            costs = x[1:]

            result = {}
            for key in x[0].keys():
                # Convert to float
                result[key] = {}
                if key.find("(m)") != -1:
                    result[key] = [float(cost[key]) for cost in costs]
                    continue
                if coefficient[key] != "":
                    result[key]["coefficient"] = float(coefficient[key])
                result[key]["cost"] = [float(cost[key]) for cost in costs]
            equipment_data[file] = result

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        dump(equipment_data, f, indent=2)


def load_json() -> dict[str, dict[str, dict[str, list[float] | float]]]:
    """
    Loads the JSON file for equipment

    Returns
    -------
    dict[str, dict[str, dict[str, list[float] | float]]]
        The JSON data for equipment
    """
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return load(f)


data = load_json()

# Constants

g = 9.80665

PIPE_LENGTH_SECTION_1 = 7.67
PIPE_LENGTH_SECTION_2 = 6.1
PIPE_LENGTH_SECTION_3 = 3.05
PIPE_LENGTH_SECTION_4 = 3.05
PIPE_LENGTH_SECTION_5 = 3.05
PIPE_TOTAL_LENGTH = (
    PIPE_LENGTH_SECTION_1
    + PIPE_LENGTH_SECTION_2
    + PIPE_LENGTH_SECTION_3
    + PIPE_LENGTH_SECTION_4
    + PIPE_LENGTH_SECTION_5
)

NUM_BENDS_SECTION_2 = 2

name = 0


def optimal(vol_flow: float, file: str, recurse: bool = False) -> None:
    """
    Calculates the optimal equipment configuration for an ethanol production
    plant

    Parameters
    ----------
    vol_flow : float
        The volumetric flow rate
    file : str
        The file to write to
    recurse : bool, optional
        Whether or not to recurse, by default False
    """
    with open(f"{file}", "a+", encoding="utf-8") as f:
        # Fermenter in calculations
        fermenter_in = {
            "initial_volumetric_flow": vol_flow,
            "density_sugar": 1599,
            "density_ethanol": 789,
            "density_fiber": 1311,
            "density_water": 997,
        }
        fermenter_in["mass"] = fermenter_in["initial_volumetric_flow"] * 1182

        pipe_diameter = 0.15
        pipe_data = {"coefficient": 0.002, "cost": 73}
        valve_data = {"coefficient": 500.0, "cost": 76}

        # Fermenter calculations
        for fermenter_name, fermenter_data in data["fermenters"].items():
            fermenter_out = {
                "fermenter_name": fermenter_name,
                "kinetic_energy_flow_out": (
                    0.5
                    * fermenter_in["mass"]
                    * (
                        fermenter_in["initial_volumetric_flow"]
                        / ((pipe_diameter / 2) ** 2)
                    )
                    ** 2
                ),
                "initial_volumetric_flow": fermenter_in[
                    "initial_volumetric_flow"
                ],
                "mass_water": 0.6 * fermenter_in["mass"],
                "mass_fiber": 0.2 * fermenter_in["mass"],
                "mass_sugar": (
                    0.2
                    * fermenter_in["mass"]
                    * (1 - fermenter_data["efficiency"])  # type: ignore
                ),
                "mass_ethanol": 0.51
                * 0.2
                * fermenter_in["mass"]
                * fermenter_data["efficiency"],
                "mass_co2": 0.49
                * 0.2
                * fermenter_in["mass"]
                * fermenter_data["efficiency"],
            }
            fermenter_out["total_mass"] = (
                fermenter_out["mass_water"]
                + fermenter_out["mass_fiber"]
                + fermenter_out["mass_sugar"]
                + fermenter_out["mass_ethanol"]
            )
            fermenter_out["density"] = (
                fermenter_in["density_sugar"] * fermenter_out["mass_sugar"]
                + fermenter_in["density_water"] * fermenter_out["mass_water"]
                + fermenter_in["density_ethanol"]
                * fermenter_out["mass_ethanol"]
                + fermenter_in["density_fiber"] * fermenter_out["mass_fiber"]
            ) / fermenter_out["total_mass"]
            fermenter_out["volumetric_flow"] = (
                fermenter_out["total_mass"] / fermenter_out["density"]
            )

            # Energy loss calculations
            bend_energy_loss_2 = (
                NUM_BENDS_SECTION_2
                * fermenter_out["total_mass"]
                * 0.3
                * (
                    fermenter_out["volumetric_flow"]
                    / 86400
                    / (pi * ((pipe_diameter / 2) ** 2))
                )
                ** 2
                / (2 * g)
            ) / (3.6e6)

            pipe_energy_loss_2 = (
                fermenter_out["total_mass"]
                * g
                * (
                    pipe_data["coefficient"]
                    * 8
                    * (fermenter_out["volumetric_flow"] / 86400) ** 2
                    * PIPE_LENGTH_SECTION_2
                    / (pi**2 * g * ((pipe_diameter / 2) * 2) ** 5)
                )
            ) / (3.6e6)

            valve_energy_loss_2 = (
                2
                * (
                    fermenter_out["total_mass"]
                    * g
                    * valve_data["coefficient"]
                    * (
                        (fermenter_out["volumetric_flow"] / 86400)
                        / (pi * (pipe_diameter / 2) ** 2)
                    )
                    ** 2
                    / (2 * g)
                )
                / (3.6e6)
            )

            total_energy_loss_2 = (
                bend_energy_loss_2
                + pipe_energy_loss_2
                + valve_energy_loss_2
                - (fermenter_out["total_mass"] * g * PIPE_LENGTH_SECTION_2)
                / (3.6e6)
            )

            # Fermenter out calculations
            fermenter_out["mass_sugar"] -= (
                cbrt(
                    fermenter_in["density_sugar"] ** 2
                    * ((pipe_diameter / 2) * 2) ** 4
                    * total_energy_loss_2
                )
                / 2
            )
            fermenter_out["mass_water"] -= (
                cbrt(
                    fermenter_in["density_water"] ** 2
                    * ((pipe_diameter / 2) * 2) ** 4
                    * total_energy_loss_2
                )
                / 2
            )
            fermenter_out["mass_fiber"] -= (
                cbrt(
                    fermenter_in["density_fiber"] ** 2
                    * ((pipe_diameter / 2) * 2) ** 4
                    * total_energy_loss_2
                )
                / 2
            )
            fermenter_out["mass_ethanol"] -= (
                cbrt(
                    fermenter_in["density_ethanol"] ** 2
                    * ((pipe_diameter / 2) * 2) ** 4
                    * total_energy_loss_2
                )
                / 2
            )

            fermenter_out["total_mass"] = (
                fermenter_out["mass_water"]
                + fermenter_out["mass_fiber"]
                + fermenter_out["mass_sugar"]
                + fermenter_out["mass_ethanol"]
            )
            fermenter_out["density"] = (
                fermenter_in["density_sugar"] * fermenter_out["mass_sugar"]
                + fermenter_in["density_water"] * fermenter_out["mass_water"]
                + fermenter_in["density_ethanol"]
                * fermenter_out["mass_ethanol"]
                + fermenter_in["density_fiber"] * fermenter_out["mass_fiber"]
            ) / fermenter_out["total_mass"]
            fermenter_out["volumetric_flow"] = (
                fermenter_out["total_mass"] / fermenter_out["density"]
            )

            for filter_name, filter_data in data["filters"].items():
                # Filter calculations
                filter_in = fermenter_out.copy()
                filter_out = filter_in.copy()

                filter_out["filter_name"] = filter_name
                filter_out["mass_fiber"] = filter_in["mass_fiber"] * (
                    1 - filter_data["efficiency"]
                )  # type: ignore
                filter_out["mass_fiber_waste_filter"] = (
                    filter_in["mass_fiber"] * filter_data["efficiency"]
                )
                filter_out["total_mass"] = (
                    filter_out["mass_water"]
                    + filter_out["mass_fiber"]
                    + filter_out["mass_sugar"]
                    + filter_out["mass_ethanol"]
                )
                filter_out["density"] = (
                    fermenter_in["density_sugar"] * filter_out["mass_sugar"]
                    + fermenter_in["density_water"] * filter_out["mass_water"]
                    + fermenter_in["density_ethanol"]
                    * filter_out["mass_ethanol"]
                    + fermenter_in["density_fiber"] * filter_out["mass_fiber"]
                ) / filter_out["total_mass"]
                filter_out["volumetric_flow"] = (
                    filter_out["total_mass"] / filter_out["density"]
                )

                # Energy loss calculations
                pipe_energy_loss_3 = (
                    filter_out["total_mass"]
                    * g
                    * pipe_data["coefficient"]
                    * 8
                    * (filter_out["volumetric_flow"] / 86400) ** 2
                    * PIPE_LENGTH_SECTION_3
                    / (pi**2 * g * ((pipe_diameter / 2) * 2) ** 5)
                ) / (3.6e6)

                valve_energy_loss_3 = (
                    2
                    * filter_out["total_mass"]
                    * g
                    * valve_data["coefficient"]
                    * (
                        (filter_out["volumetric_flow"] / 86400)
                        / (pi * (pipe_diameter / 2) ** 2)
                    )
                    ** 2
                    / (2 * g)
                ) / (3.6e6)

                total_energy_loss_3 = pipe_energy_loss_3 + valve_energy_loss_3

                # Filter out calculations
                filter_out["mass_sugar"] -= (
                    cbrt(
                        fermenter_in["density_sugar"] ** 2
                        * ((pipe_diameter / 2) * 2) ** 4
                        * total_energy_loss_3
                    )
                    / 2
                )
                filter_out["mass_water"] -= (
                    cbrt(
                        fermenter_in["density_water"] ** 2
                        * ((pipe_diameter / 2) * 2) ** 4
                        * total_energy_loss_3
                    )
                    / 2
                )
                filter_out["mass_fiber"] -= (
                    cbrt(
                        fermenter_in["density_fiber"] ** 2
                        * ((pipe_diameter / 2) * 2) ** 4
                        * total_energy_loss_3
                    )
                    / 2
                )
                filter_out["mass_ethanol"] -= (
                    cbrt(
                        fermenter_in["density_ethanol"] ** 2
                        * ((pipe_diameter / 2) * 2) ** 4
                        * total_energy_loss_3
                    )
                    / 2
                )

                filter_out["total_mass"] = (
                    filter_out["mass_water"]
                    + filter_out["mass_fiber"]
                    + filter_out["mass_sugar"]
                    + filter_out["mass_ethanol"]
                )
                filter_out["density"] = (
                    fermenter_in["density_sugar"] * filter_out["mass_sugar"]
                    + fermenter_in["density_water"] * filter_out["mass_water"]
                    + fermenter_in["density_ethanol"]
                    * filter_out["mass_ethanol"]
                    + fermenter_in["density_fiber"] * filter_out["mass_fiber"]
                ) / filter_out["total_mass"]
                filter_out["volumetric_flow"] = (
                    filter_out["total_mass"] / filter_out["density"]
                )

                for distiller_name, distiller_data in data[
                    "distillers"
                ].items():
                    # Distiller calculations
                    distiller_in = filter_out.copy()
                    distiller_out = distiller_in.copy()

                    divisor = (
                        distiller_in["mass_water"]
                        + distiller_in["mass_sugar"]
                        + distiller_in["mass_fiber"]
                    )

                    distiller_out["distiller_name"] = distiller_name
                    distiller_out["mass_fiber"] = (
                        distiller_in["mass_fiber"]
                        * distiller_in["mass_ethanol"]
                        * (1 / distiller_data["efficiency"] - 1)  # type: ignore
                        / divisor
                    )
                    distiller_out["mass_water"] = (
                        distiller_in["mass_water"]
                        * distiller_in["mass_ethanol"]
                        * (1 / distiller_data["efficiency"] - 1)  # type: ignore
                        / divisor
                    )
                    distiller_out["mass_sugar"] = (
                        distiller_in["mass_sugar"]
                        * distiller_in["mass_ethanol"]
                        * (1 / distiller_data["efficiency"] - 1)  # type: ignore
                        / divisor
                    )

                    distiller_out["mass_fiber_waste_distiller"] = (
                        distiller_in["mass_fiber"] - distiller_out["mass_fiber"]
                    )
                    distiller_out["mass_sugar_waste_distiller"] = (
                        distiller_in["mass_sugar"] - distiller_out["mass_sugar"]
                    )
                    distiller_out["mass_water_waste_distiller"] = (
                        distiller_in["mass_water"] - distiller_out["mass_water"]
                    )

                    distiller_out["total_mass"] = (
                        distiller_out["mass_water"]
                        + distiller_out["mass_fiber"]
                        + distiller_out["mass_sugar"]
                        + distiller_out["mass_ethanol"]
                    )
                    distiller_out["density"] = (
                        fermenter_in["density_sugar"]
                        * distiller_out["mass_sugar"]
                        + fermenter_in["density_water"]
                        * distiller_out["mass_water"]
                        + fermenter_in["density_ethanol"]
                        * distiller_out["mass_ethanol"]
                        + fermenter_in["density_fiber"]
                        * distiller_out["mass_fiber"]
                    ) / distiller_out["total_mass"]
                    distiller_out["volumetric_flow"] = (
                        distiller_out["total_mass"] / distiller_out["density"]
                    )

                    # Energy loss calculations
                    pipe_energy_loss_4 = (
                        distiller_out["total_mass"]
                        * g
                        * (
                            pipe_data["coefficient"]
                            * 8
                            * (distiller_out["volumetric_flow"] / 86400) ** 2
                            * PIPE_LENGTH_SECTION_4
                            / (pi**2 * g * ((pipe_diameter / 2) * 2) ** 5)
                        )
                    ) / (3.6e6)

                    valve_energy_loss_4 = (
                        2
                        * (
                            distiller_out["total_mass"]
                            * g
                            * valve_data["coefficient"]
                            * (
                                (distiller_out["volumetric_flow"] / 86400)
                                / (pi * (pipe_diameter / 2) ** 2)
                            )
                            ** 2
                            / (2 * g)
                        )
                        / (3.6e6)
                    )

                    total_energy_loss_4 = (
                        pipe_energy_loss_4 + valve_energy_loss_4
                    )

                    # Distiller out calculations
                    distiller_out["mass_sugar"] -= (
                        cbrt(
                            fermenter_in["density_sugar"] ** 2
                            * ((pipe_diameter / 2) * 2) ** 4
                            * total_energy_loss_4
                        )
                        / 2
                    )
                    distiller_out["mass_water"] -= (
                        cbrt(
                            fermenter_in["density_water"] ** 2
                            * ((pipe_diameter / 2) * 2) ** 4
                            * total_energy_loss_4
                        )
                        / 2
                    )
                    distiller_out["mass_fiber"] -= (
                        cbrt(
                            fermenter_in["density_fiber"] ** 2
                            * ((pipe_diameter / 2) * 2) ** 4
                            * total_energy_loss_4
                        )
                        / 2
                    )
                    distiller_out["mass_ethanol"] -= (
                        cbrt(
                            fermenter_in["density_ethanol"] ** 2
                            * ((pipe_diameter / 2) * 2) ** 4
                            * total_energy_loss_4
                        )
                        / 2
                    )

                    distiller_out["total_mass"] = (
                        distiller_out["mass_water"]
                        + distiller_out["mass_fiber"]
                        + distiller_out["mass_sugar"]
                        + distiller_out["mass_ethanol"]
                    )
                    distiller_out["density"] = (
                        fermenter_in["density_sugar"]
                        * distiller_out["mass_sugar"]
                        + fermenter_in["density_water"]
                        * distiller_out["mass_water"]
                        + fermenter_in["density_ethanol"]
                        * distiller_out["mass_ethanol"]
                        + fermenter_in["density_fiber"]
                        * distiller_out["mass_fiber"]
                    ) / distiller_out["total_mass"]
                    distiller_out["volumetric_flow"] = (
                        distiller_out["total_mass"] / distiller_out["density"]
                    )

                    for dehydrator_name, dehydrator_data in data[
                        "filters"
                    ].items():
                        # Dehydrator calculations
                        dehydrator_in = distiller_out.copy()
                        dehydrator_out = dehydrator_in.copy()

                        dehydrator_out["dehydrator_name"] = dehydrator_name
                        dehydrator_out["mass_water"] = dehydrator_in[
                            "mass_water"
                        ] * (
                            1 - dehydrator_data["efficiency"]
                        )  # type: ignore
                        dehydrator_out["mass_water_waste_dehydrator"] = (
                            dehydrator_in["mass_water"]
                            * dehydrator_data["efficiency"]
                        )
                        dehydrator_out["total_mass"] = (
                            dehydrator_out["mass_water"]
                            + dehydrator_out["mass_fiber"]
                            + dehydrator_out["mass_sugar"]
                            + dehydrator_out["mass_ethanol"]
                        )
                        dehydrator_out["density"] = (
                            fermenter_in["density_sugar"]
                            * dehydrator_out["mass_sugar"]
                            + fermenter_in["density_water"]
                            * dehydrator_out["mass_water"]
                            + fermenter_in["density_ethanol"]
                            * dehydrator_out["mass_ethanol"]
                            + fermenter_in["density_fiber"]
                            * dehydrator_out["mass_fiber"]
                        ) / dehydrator_out["total_mass"]
                        dehydrator_out["volumetric_flow"] = (
                            dehydrator_out["total_mass"]
                            / dehydrator_out["density"]
                        )

                        # Energy loss calculations
                        pipe_energy_loss_5 = (
                            dehydrator_out["total_mass"]
                            * g
                            * (
                                pipe_data["coefficient"]
                                * 8
                                * (dehydrator_out["volumetric_flow"] / 86400)
                                ** 2
                                * PIPE_LENGTH_SECTION_5
                                / (pi**2 * g * ((pipe_diameter / 2) * 2) ** 5)
                            )
                        ) / (3.6e6)

                        valve_energy_loss_5 = (
                            dehydrator_out["total_mass"]
                            * g
                            * valve_data["coefficient"]
                            * (
                                (dehydrator_out["volumetric_flow"] / 86400)
                                / (pi * (pipe_diameter / 2) ** 2)
                            )
                            ** 2
                            / (2 * g)
                        ) / (3.6e6)

                        total_energy_loss_5 = (
                            pipe_energy_loss_5 + valve_energy_loss_5
                        )

                        # Dehydrator out calculations
                        dehydrator_out["mass_sugar"] -= (
                            cbrt(
                                fermenter_in["density_sugar"] ** 2
                                * ((pipe_diameter / 2) * 2) ** 4
                                * total_energy_loss_5
                            )
                            / 2
                        )
                        dehydrator_out["mass_water"] -= (
                            cbrt(
                                fermenter_in["density_water"] ** 2
                                * ((pipe_diameter / 2) * 2) ** 4
                                * total_energy_loss_5
                            )
                            / 2
                        )
                        dehydrator_out["mass_fiber"] -= (
                            cbrt(
                                fermenter_in["density_fiber"] ** 2
                                * ((pipe_diameter / 2) * 2) ** 4
                                * total_energy_loss_5
                            )
                            / 2
                        )
                        dehydrator_out["mass_ethanol"] -= (
                            cbrt(
                                fermenter_in["density_ethanol"] ** 2
                                * ((pipe_diameter / 2) * 2) ** 4
                                * total_energy_loss_5
                            )
                            / 2
                        )
                        dehydrator_out["total_mass"] = (
                            dehydrator_out["mass_water"]
                            + dehydrator_out["mass_fiber"]
                            + dehydrator_out["mass_sugar"]
                            + dehydrator_out["mass_ethanol"]
                        )

                        dehydrator_out["density"] = (
                            fermenter_in["density_sugar"]
                            * dehydrator_out["mass_sugar"]
                            + fermenter_in["density_water"]
                            * dehydrator_out["mass_water"]
                            + fermenter_in["density_ethanol"]
                            * dehydrator_out["mass_ethanol"]
                            + fermenter_in["density_fiber"]
                            * dehydrator_out["mass_fiber"]
                        ) / dehydrator_out["total_mass"]
                        dehydrator_out["volumetric_flow"] = (
                            dehydrator_out["total_mass"]
                            / dehydrator_out["density"]
                        )

                        # Cost calculations
                        cost = (
                            fermenter_data["cost"]
                            * fermenter_in["initial_volumetric_flow"]
                            + filter_data["cost"] * filter_in["volumetric_flow"]
                            + distiller_data["cost"]
                            * distiller_in["volumetric_flow"]
                            + dehydrator_data["cost"]
                            * dehydrator_in["volumetric_flow"]
                        ) / 24

                        cost += pipe_data["cost"] * PIPE_TOTAL_LENGTH
                        cost += valve_data["cost"] * 8
                        cost += 19 * fermenter_in["initial_volumetric_flow"]
                        cost += (
                            4 * data["bends"]["90"]["cost"][-1]  # type: ignore
                        )
                        cost += (
                            456 * fermenter_in["initial_volumetric_flow"] / 24
                        )

                        dehydrator_out["total_cost"] = cost

                        # Filter out suboptimal results
                        grade = (
                            dehydrator_out["mass_ethanol"]
                            / dehydrator_out["total_mass"]
                        )
                        if float(grade) < 0.98:
                            continue

                        if not recurse:
                            if dehydrator_out["volumetric_flow"] < 378:
                                continue

                            if dehydrator_out["volumetric_flow"] > 379:
                                continue

                        # Write to file
                        json_str = dumps(
                            {
                                "Q In": dehydrator_out[
                                    "initial_volumetric_flow"
                                ],
                                "Q Out": dehydrator_out["volumetric_flow"],
                                "Fermenter": fermenter_out["fermenter_name"],
                                "Filter": filter_out["filter_name"],
                                "Distiller": distiller_out["distiller_name"],
                                "Dehydrator": dehydrator_out["dehydrator_name"],
                                "Cost": dehydrator_out["total_cost"],
                                "Pump Energy": fermenter_in["mass"]
                                * g
                                * 9
                                / (3.6e6),
                                "Mass CO2": fermenter_out["mass_co2"],
                            },
                            indent=2,
                        )
                        json_str = (
                            json_str.split("\n")[0]
                            + "\n"
                            + "\n".join(
                                "  " + line for line in json_str.split("\n")[1:]
                            )
                        )
                        global name
                        f.write(f'  "x{name}": ' + json_str)
                        name += 1
                        f.write(",\n")

                        # Recurse
                        if recurse:
                            optimal(
                                378.54118 / dehydrator_out["volumetric_flow"],
                                "flow.json",
                                False,
                            )


def fix_end_of_json(filename) -> None:
    """
    Fixes the end of the JSON file

    Parameters
    ----------
    filename : str
        The file to fix
    """
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            lines[i] = lines[i].rstrip(",\n") + "\n"
            break

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)
        f.write("}\n")


def generate() -> None:
    """
    Generates potential equipment configurations
    """
    with open("1.json", "w+", encoding="utf-8") as f:
        f.write("{\n")
    with open("flow.json", "w+", encoding="utf-8") as f:
        f.write("{\n")

    optimal(1, "1.json", True)

    fix_end_of_json("1.json")
    fix_end_of_json("flow.json")


x_values = []
y_values = []
capital = []
fermenters = []
filters = []
distillers = []
dehydrators = []
q_in = []
q_out = []

max_roi = 0
max_capital = 0
max_index = 0
max_fermenter = 0
max_filter = 0
max_distiller = 0
max_dehydrator = 0


def init_roi() -> None:
    """
    Initializes data for ROI calculations
    """
    global max_roi, max_capital, max_fermenter, max_filter
    global max_distiller, max_dehydrator, max_index

    with open("flow.json", encoding="utf-8") as f:
        roi_data = load(f)

    kWh_per_cubic_meter_ethanol = 5877.83

    with open("equipment.json", encoding="utf-8") as f:
        equipment = load(f)
        for value in roi_data.values():
            # Calculate values for ROI
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
            capital.append(value["Cost"] + 1.4e6 + 3.5 * 76 * 3 + 3.5 * 700)
            fermenters.append(value["Fermenter"])
            filters.append(value["Filter"])
            distillers.append(value["Distiller"])
            dehydrators.append(value["Dehydrator"])
            q_in.append(value["Q In"])
            q_out.append(value["Q Out"])

    # Calculate maximum ROI
    roi = []
    for i, x in enumerate(x_values):
        roi.append(y_values[i] / x)

    max_val = max(roi)
    max_index = roi.index(max_val)
    max_roi = roi[max_index]
    max_capital = capital[max_index]
    max_fermenter = fermenters[max_index]
    max_filter = filters[max_index]
    max_distiller = distillers[max_index]
    max_dehydrator = dehydrators[max_index]


def print_best() -> None:
    """
    Prints the best equipment configuration
    Pump, Pipe, Valve, and Diameter are hard coded because of our assumptions
    """
    print(
        dedent(
            f"""
        Max ROI: {max_roi:.2f}
        Q In: {264.172052 * q_in[max_index]:.2f} gal/day
        Q Out: {264.172052 * q_out[max_index]:.2f} gal/day
        Input: {x_values[max_index]:.2f} kWh/day
        Output: {y_values[max_index]:.2f} kWh/day
        Capital: {max_capital:.2f} dollars
        Best Fermenter: {max_fermenter}
        Best Filter: {max_filter}
        Best Distiller: {max_distiller}
        Best Dehydrator: {max_dehydrator}
        Best Pump: Premium
        Best Pipe: Glorious
        Best Valve: Glorious
        Diameter: 0.15 m
        """
        )
    )


def create_plot() -> None:
    """
    Creates a plot of ROI
    """
    plt.scatter(x_values, y_values)
    plt.scatter(x_values[max_index], y_values[max_index], color="red")

    plt.xlabel("kWh per day input")
    plt.ylabel("kWh per day output")
    plt.title("ROI")

    plt.ticklabel_format(style="sci", axis="both", scilimits=(0, 0))

    plt.show()


def roi_to_csv() -> None:
    """
    Outputs ROI data to a CSV file
    """
    with open("roi.csv", "w", encoding="utf-8", newline="") as f:
        writer(f).writerows(zip(x_values, y_values))


# Run the program based on arguments
if args.generate_json:
    generate_json()

if args.generate_configs:
    generate()

if __name__ == "__main__":
    init_roi()
    print_best()

if args.print_data:
    print(data)

if args.calculate_roi:
    roi_to_csv()

if args.create_plot:
    create_plot()
