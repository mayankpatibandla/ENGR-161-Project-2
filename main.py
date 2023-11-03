import multiprocessing
import os
import sys
from argparse import ArgumentParser
from json import dump, dumps
from math import cbrt, pi

import numpy as np

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

g = 9.80665

pipe_length_section_1 = 7.67
pipe_length_section_2 = 6.1
pipe_length_section_3 = 3.05
pipe_length_section_4 = 3.05
pipe_length_section_5 = 3.05
pipe_total_length = (
    pipe_length_section_1
    + pipe_length_section_2
    + pipe_length_section_3
    + pipe_length_section_4
    + pipe_length_section_5
)

num_bends_section_2 = 2

jobs = []
MAX_PROCESSES = 24

name = 0


def q(vol_flow: float, file: str, recurse: bool = False):
    with open(f"{file}", "a+", encoding='utf-8') as f:
        fermenter_in = {
            "initial_volumetric_flow": vol_flow,
            "density_sugar": 1599,
            "density_ethanol": 789,
            "density_fiber": 1311,
            "density_water": 997,
        }
        fermenter_in["mass"] = fermenter_in["initial_volumetric_flow"] * 1182

        # for pump_name, pump_data in data["pumps"].items():
        #     if pump_name.find('(m)') != -1:
        #         continue

        #     x = pump_data["cost"][2]  # type: ignore
        # pump_energy_loss_1 = fermenter_in["mass"] * g * pipe_length_section_1 / (3.6e6 * pump_data["coefficient"]) - fermenter_in["mass"] * g * pipe_length_section_1 / (3.6e6)  # type: ignore

        # bend_energy_loss_1 = (
        #     num_bends_section_1
        #     * fermenter_in["mass"]
        #     * 0.3
        #     * (fermenter_in["initial_volumetric_flow"] / 86400 / (pi * ((pipe_diameter / 2)**2))) ** 2
        #     / (2 * g)
        # ) / (3.6e6)

        # for pipe_name, pipe_data in data["pipes"].items():
        #     if pipe_name.find('(m)') != -1:
        #         continue

        #     for pipe_index, pipe_diameter in enumerate(data["pipes"]["Internal Diameter (m)"]):
        #         for valve_name, valve_data in data["valves"].items():
        #             if valve_name.find('(m)') != -1:
        #                 continue
        pipe_diameter = 0.15
        pipe_data = {"coefficient": 0.002, "cost": 73}
        valve_data = {"coefficient": 500.0, "cost": 76}

        for fermenter_name, fermenter_data in data["fermenters"].items():
            fermenter_out = {
                "fermenter_name": fermenter_name,
                "kinetic_energy_flow_out": 0.5 * fermenter_in["mass"] * (fermenter_in["initial_volumetric_flow"] / ((pipe_diameter / 2) ** 2)) ** 2,  # type: ignore
                "initial_volumetric_flow": fermenter_in["initial_volumetric_flow"],
                "mass_water": 0.6 * fermenter_in["mass"],
                "mass_fiber": 0.2 * fermenter_in["mass"],
                "mass_sugar": 0.2 * fermenter_in["mass"] * (1 - fermenter_data["efficiency"]),  # type: ignore
                "mass_ethanol": 0.51 * 0.2 * fermenter_in["mass"] * fermenter_data["efficiency"],  # type: ignore
                "mass_co2": 0.49 * 0.2 * fermenter_in["mass"] * fermenter_data["efficiency"],  # type: ignore
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
                + fermenter_in["density_ethanol"] * fermenter_out["mass_ethanol"]
                + fermenter_in["density_fiber"] * fermenter_out["mass_fiber"]
            ) / fermenter_out["total_mass"]
            fermenter_out["volumetric_flow"] = fermenter_out["total_mass"] / fermenter_out["density"]
            # print(fermenter_out)

            bend_energy_loss_2 = (
                num_bends_section_2
                * fermenter_out["total_mass"]
                * 0.3
                * (fermenter_out["volumetric_flow"] / 86400 / (pi * ((pipe_diameter / 2) ** 2))) ** 2  # type: ignore
                / (2 * g)
            ) / (3.6e6)

            # print(fermenter_out["total_mass"])
            # print(pipe_data["coefficient"])
            # print(valve_data["coefficient"])
            # print(fermenter_out["volumetric_flow"])
            # print(pipe_diameter)
            # print(pipe_length_section_2)
            pipe_energy_loss_2 = (fermenter_out["total_mass"] * g * (pipe_data["coefficient"] * 8 * (fermenter_out["volumetric_flow"] / 86400) ** 2 * pipe_length_section_2 / (pi**2 * g * ((pipe_diameter / 2) * 2) ** 5))) / (3.6e6)  # type: ignore

            valve_energy_loss_2 = 2 * (fermenter_out["total_mass"] * g * valve_data["coefficient"] * ((fermenter_out["volumetric_flow"] / 86400) / (pi * (pipe_diameter / 2) ** 2)) ** 2 / (2 * g)) / (3.6e6)  # type: ignore

            total_energy_loss_2 = (
                bend_energy_loss_2
                + pipe_energy_loss_2
                + valve_energy_loss_2
                - (fermenter_out["total_mass"] * g * pipe_length_section_2) / (3.6e6)
            )

            fermenter_out["mass_sugar"] -= cbrt(fermenter_in["density_sugar"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_2) / 2  # type: ignore
            fermenter_out["mass_water"] -= cbrt(fermenter_in["density_water"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_2) / 2  # type: ignore
            fermenter_out["mass_fiber"] -= cbrt(fermenter_in["density_fiber"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_2) / 2  # type: ignore
            fermenter_out["mass_ethanol"] -= cbrt(fermenter_in["density_ethanol"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_2) / 2  # type: ignore

            fermenter_out["total_mass"] = (
                fermenter_out["mass_water"]
                + fermenter_out["mass_fiber"]
                + fermenter_out["mass_sugar"]
                + fermenter_out["mass_ethanol"]
            )
            fermenter_out["density"] = (
                fermenter_in["density_sugar"] * fermenter_out["mass_sugar"]
                + fermenter_in["density_water"] * fermenter_out["mass_water"]
                + fermenter_in["density_ethanol"] * fermenter_out["mass_ethanol"]
                + fermenter_in["density_fiber"] * fermenter_out["mass_fiber"]
            ) / fermenter_out["total_mass"]
            fermenter_out["volumetric_flow"] = fermenter_out["total_mass"] / fermenter_out["density"]

            for filter_name, filter_data in data["filters"].items():
                filter_in = fermenter_out.copy()
                filter_out = filter_in.copy()

                filter_out["filter_name"] = filter_name
                filter_out["mass_fiber"] = filter_in["mass_fiber"] * (1 - filter_data["efficiency"])  # type: ignore
                filter_out["mass_fiber_waste_filter"] = filter_in["mass_fiber"] * filter_data["efficiency"]
                filter_out["total_mass"] = (
                    filter_out["mass_water"]
                    + filter_out["mass_fiber"]
                    + filter_out["mass_sugar"]
                    + filter_out["mass_ethanol"]
                )
                filter_out["density"] = (
                    fermenter_in["density_sugar"] * filter_out["mass_sugar"]
                    + fermenter_in["density_water"] * filter_out["mass_water"]
                    + fermenter_in["density_ethanol"] * filter_out["mass_ethanol"]
                    + fermenter_in["density_fiber"] * filter_out["mass_fiber"]
                ) / filter_out["total_mass"]
                filter_out["volumetric_flow"] = filter_out["total_mass"] / filter_out["density"]

                # print(filter_out)

                pipe_energy_loss_3 = (filter_out["total_mass"] * g * (pipe_data["coefficient"] * 8 * (filter_out["volumetric_flow"] / 86400) ** 2 * pipe_length_section_3 / (pi**2 * g * ((pipe_diameter / 2) * 2) ** 5))) / (3.6e6)  # type: ignore

                valve_energy_loss_3 = 2 * (filter_out["total_mass"] * g * valve_data["coefficient"] * ((filter_out["volumetric_flow"] / 86400) / (pi * (pipe_diameter / 2) ** 2)) ** 2 / (2 * g)) / (3.6e6)  # type: ignore

                total_energy_loss_3 = pipe_energy_loss_3 + valve_energy_loss_3

                filter_out["mass_sugar"] -= cbrt(fermenter_in["density_sugar"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_3) / 2  # type: ignore
                filter_out["mass_water"] -= cbrt(fermenter_in["density_water"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_3) / 2  # type: ignore
                filter_out["mass_fiber"] -= cbrt(fermenter_in["density_fiber"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_3) / 2  # type: ignore
                filter_out["mass_ethanol"] -= cbrt(fermenter_in["density_ethanol"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_3) / 2  # type: ignore

                filter_out["total_mass"] = (
                    filter_out["mass_water"]
                    + filter_out["mass_fiber"]
                    + filter_out["mass_sugar"]
                    + filter_out["mass_ethanol"]
                )
                filter_out["density"] = (
                    fermenter_in["density_sugar"] * filter_out["mass_sugar"]
                    + fermenter_in["density_water"] * filter_out["mass_water"]
                    + fermenter_in["density_ethanol"] * filter_out["mass_ethanol"]
                    + fermenter_in["density_fiber"] * filter_out["mass_fiber"]
                ) / filter_out["total_mass"]
                filter_out["volumetric_flow"] = filter_out["total_mass"] / filter_out["density"]

                for distiller_name, distiller_data in data["distillers"].items():
                    distiller_in = filter_out.copy()
                    distiller_out = distiller_in.copy()

                    divisor = distiller_in["mass_water"] + distiller_in["mass_sugar"] + distiller_in["mass_fiber"]

                    distiller_out["distiller_name"] = distiller_name
                    distiller_out["mass_fiber"] = distiller_in["mass_fiber"] * distiller_in["mass_ethanol"] * (1 / distiller_data["efficiency"] - 1) / divisor  # type: ignore
                    distiller_out["mass_water"] = distiller_in["mass_water"] * distiller_in["mass_ethanol"] * (1 / distiller_data["efficiency"] - 1) / divisor  # type: ignore
                    distiller_out["mass_sugar"] = distiller_in["mass_sugar"] * distiller_in["mass_ethanol"] * (1 / distiller_data["efficiency"] - 1) / divisor  # type: ignore

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
                        fermenter_in["density_sugar"] * distiller_out["mass_sugar"]
                        + fermenter_in["density_water"] * distiller_out["mass_water"]
                        + fermenter_in["density_ethanol"] * distiller_out["mass_ethanol"]
                        + fermenter_in["density_fiber"] * distiller_out["mass_fiber"]
                    ) / distiller_out["total_mass"]
                    distiller_out["volumetric_flow"] = distiller_out["total_mass"] / distiller_out["density"]

                    # print(distiller_out)

                    pipe_energy_loss_4 = (distiller_out["total_mass"] * g * (pipe_data["coefficient"] * 8 * (distiller_out["volumetric_flow"] / 86400) ** 2 * pipe_length_section_4 / (pi**2 * g * ((pipe_diameter / 2) * 2) ** 5))) / (3.6e6)  # type: ignore

                    valve_energy_loss_4 = 2 * (distiller_out["total_mass"] * g * valve_data["coefficient"] * ((distiller_out["volumetric_flow"] / 86400) / (pi * (pipe_diameter / 2) ** 2)) ** 2 / (2 * g)) / (3.6e6)  # type: ignore

                    total_energy_loss_4 = pipe_energy_loss_4 + valve_energy_loss_4

                    distiller_out["mass_sugar"] -= cbrt(fermenter_in["density_sugar"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_4) / 2  # type: ignore
                    distiller_out["mass_water"] -= cbrt(fermenter_in["density_water"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_4) / 2  # type: ignore
                    distiller_out["mass_fiber"] -= cbrt(fermenter_in["density_fiber"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_4) / 2  # type: ignore
                    distiller_out["mass_ethanol"] -= cbrt(fermenter_in["density_ethanol"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_4) / 2  # type: ignore

                    distiller_out["total_mass"] = (
                        distiller_out["mass_water"]
                        + distiller_out["mass_fiber"]
                        + distiller_out["mass_sugar"]
                        + distiller_out["mass_ethanol"]
                    )
                    distiller_out["density"] = (
                        fermenter_in["density_sugar"] * distiller_out["mass_sugar"]
                        + fermenter_in["density_water"] * distiller_out["mass_water"]
                        + fermenter_in["density_ethanol"] * distiller_out["mass_ethanol"]
                        + fermenter_in["density_fiber"] * distiller_out["mass_fiber"]
                    ) / distiller_out["total_mass"]
                    distiller_out["volumetric_flow"] = distiller_out["total_mass"] / distiller_out["density"]

                    for dehydrator_name, dehydrator_data in data["filters"].items():
                        dehydrator_in = distiller_out.copy()
                        dehydrator_out = dehydrator_in.copy()

                        dehydrator_out["dehydrator_name"] = dehydrator_name
                        dehydrator_out["mass_water"] = dehydrator_in["mass_water"] * (1 - dehydrator_data["efficiency"])  # type: ignore
                        dehydrator_out["mass_water_waste_dehydrator"] = (
                            dehydrator_in["mass_water"] * dehydrator_data["efficiency"]
                        )
                        dehydrator_out["total_mass"] = (
                            dehydrator_out["mass_water"]
                            + dehydrator_out["mass_fiber"]
                            + dehydrator_out["mass_sugar"]
                            + dehydrator_out["mass_ethanol"]
                        )
                        dehydrator_out["density"] = (
                            fermenter_in["density_sugar"] * dehydrator_out["mass_sugar"]
                            + fermenter_in["density_water"] * dehydrator_out["mass_water"]
                            + fermenter_in["density_ethanol"] * dehydrator_out["mass_ethanol"]
                            + fermenter_in["density_fiber"] * dehydrator_out["mass_fiber"]
                        ) / dehydrator_out["total_mass"]
                        dehydrator_out["volumetric_flow"] = dehydrator_out["total_mass"] / dehydrator_out["density"]

                        pipe_energy_loss_5 = (dehydrator_out["total_mass"] * g * (pipe_data["coefficient"] * 8 * (dehydrator_out["volumetric_flow"] / 86400) ** 2 * pipe_length_section_5 / (pi**2 * g * ((pipe_diameter / 2) * 2) ** 5))) / (3.6e6)  # type: ignore

                        valve_energy_loss_5 = (dehydrator_out["total_mass"] * g * valve_data["coefficient"] * ((dehydrator_out["volumetric_flow"] / 86400) / (pi * (pipe_diameter / 2) ** 2)) ** 2 / (2 * g)) / (3.6e6)  # type: ignore

                        total_energy_loss_5 = pipe_energy_loss_5 + valve_energy_loss_5

                        dehydrator_out["mass_sugar"] -= cbrt(fermenter_in["density_sugar"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_5) / 2  # type: ignore
                        dehydrator_out["mass_water"] -= cbrt(fermenter_in["density_water"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_5) / 2  # type: ignore
                        dehydrator_out["mass_fiber"] -= cbrt(fermenter_in["density_fiber"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_5) / 2  # type: ignore
                        dehydrator_out["mass_ethanol"] -= cbrt(fermenter_in["density_ethanol"] ** 2 * ((pipe_diameter / 2) * 2) ** 4 * total_energy_loss_5) / 2  # type: ignore

                        dehydrator_out["total_mass"] = (
                            dehydrator_out["mass_water"]
                            + dehydrator_out["mass_fiber"]
                            + dehydrator_out["mass_sugar"]
                            + dehydrator_out["mass_ethanol"]
                        )
                        dehydrator_out["density"] = (
                            fermenter_in["density_sugar"] * dehydrator_out["mass_sugar"]
                            + fermenter_in["density_water"] * dehydrator_out["mass_water"]
                            + fermenter_in["density_ethanol"] * dehydrator_out["mass_ethanol"]
                            + fermenter_in["density_fiber"] * dehydrator_out["mass_fiber"]
                        ) / dehydrator_out["total_mass"]
                        dehydrator_out["volumetric_flow"] = dehydrator_out["total_mass"] / dehydrator_out["density"]

                        cost = (fermenter_data["cost"] * fermenter_in["initial_volumetric_flow"] + filter_data["cost"] * filter_in["volumetric_flow"] + distiller_data["cost"] * distiller_in["volumetric_flow"] + dehydrator_data["cost"] * dehydrator_in["volumetric_flow"]) / 24 + pipe_data["cost"] * pipe_total_length + valve_data["cost"] * 8 + (19 * fermenter_in["initial_volumetric_flow"]) + 4 * data["bends"]["90"]["cost"][-1]  # type: ignore
                        dehydrator_out["total_cost"] = cost

                        if (
                            isinstance(dehydrator_out["mass_ethanol"], complex)
                            or isinstance(dehydrator_out["mass_sugar"], complex)
                            or isinstance(dehydrator_out["mass_fiber"], complex)
                            or isinstance(dehydrator_out["mass_water"], complex)
                        ) or (
                            dehydrator_out["mass_ethanol"] < 0
                            or dehydrator_out["mass_sugar"] < 0
                            or dehydrator_out["mass_fiber"] < 0
                            or dehydrator_out["mass_water"] < 0
                        ):
                            print(fermenter_out)
                            print(filter_out)
                            print(distiller_out)
                            print(dehydrator_out)
                            print(pipe_energy_loss_4)
                            print(valve_energy_loss_4)
                            sys.exit(1)

                        grade = dehydrator_out["mass_ethanol"] / dehydrator_out["total_mass"]
                        if float(grade) < 0.98:
                            continue
                        # # print(type(dehydrator_out["mass_ethanol"]), type(dehydrator_out["total_mass"]), type(grade))

                        if not recurse:
                            if dehydrator_out["volumetric_flow"] < 378:  # type: ignore
                                continue

                            if dehydrator_out["volumetric_flow"] > 379:  # type: ignore
                                continue

                        # velocity = (2 * 9.81 * (7.62 - 0)) ** 0.5

                        # output.append(
                        #     {
                        #         # "Fermenter Out": fermenter_out,
                        #         # "Filter Out": filter_out,
                        #         # "Distiller Out": distiller_out,
                        #         # "Dehydrator Out": dehydrator_out,
                        #         # "Pump Efficiency": pump_data["coefficient"],
                        #         # "Bend Energy Loss Section 2": bend_energy_loss_2,
                        #         # "Pipe Energy Loss Section 2": pipe_energy_loss_2,
                        #         # "Valve Energy Loss Section 2": valve_energy_loss_2,
                        #         # "Mass Input": fermenter_in["mass"],
                        #         "Q": dehydrator_out["volumetric_flow"],
                        #     }
                        # )
                        # print(
                        #     dehydrator_out["volumetric_flow"],
                        #     type(dehydrator_out["volumetric_flow"]),
                        # )

                        json_str = dumps(
                            {
                                "Q In": dehydrator_out["initial_volumetric_flow"],
                                "Q Out": dehydrator_out["volumetric_flow"],
                                "Fermenter": fermenter_out["fermenter_name"],
                                "Filter": filter_out["filter_name"],
                                "Distiller": distiller_out["distiller_name"],
                                "Dehydrator": dehydrator_out["dehydrator_name"],
                                "Cost": dehydrator_out["total_cost"],
                            },
                            indent=2,
                        )
                        global name
                        f.write(f'"x{name}": '+ json_str)
                        name += 1
                        f.write(",\n")

                        global jobs
                        if recurse:
                            q(378.54118 / dehydrator_out["volumetric_flow"], "2.json", False)
                            # p = multiprocessing.Process(
                            #     target=q,
                            #     args=(
                            #         378.54118 / dehydrator_out["volumetric_flow"],
                            #         "2.json",
                            #         False,
                            #     ),
                            #     daemon=True,
                            # )
                            # jobs.append(p)
                            # jobs = [job for job in jobs if job.is_alive()]
                            # if len(jobs) >= MAX_PROCESSES:
                            #     for job in jobs:
                            #         job.join()
                            #     jobs.clear()
                            # else:
                            #     p.start()

                        # return dehydrator_out, grade
                # for pump_name, pump_data in data["pumps"].items():
                #     if pump_name.find('(m)') != -1:
                #         continue
                #     for pipe_name, pipe_data in data["pipes"].items():
                #         if pipe_name.find('(m)') != -1:
                #             continue
                #         for ductwork_name, ductwork_data in data["ductworks"].items():
                #             if ductwork_name.find('(m)') != -1:
                #                 continue
                #             for bend_angle, bend_data in data["bends"].items():
                #                 if bend_angle.find('(m)') != -1:
                #                     continue
                #                 for valve_name, valve_data in data["valves"].items():
                #                     if valve_name.find('(m)') != -1:
                #                         continue


def main(start: int, stop: int, step: int):
    try:
        os.remove("1.json")
        os.remove("2.json")
    except FileNotFoundError:
        pass

    input("Press enter to start")
    # x = {"data": [q(float(float(x) / 264.17205)) for x in np.arange(start, stop, step)]}
    # q(1, "1.json")
    # print(output["volumetric_flow"])
    # # print(grade)
    # q(378.54118 / output["volumetric_flow"], "2.json")
    q(1, "1.json", True)

    # with open("Volumetric Flow.json", "w", encoding='utf-8') as f:
    #     dump(x, f, indent=2)


if __name__ == '__main__':
    main(int(8e5), int(1.2e6), 100)
