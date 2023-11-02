from argparse import ArgumentParser
from json import dump
from math import pi

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
pipe_radius_section_1 = 0.05
pipe_radius_section_2 = 0.05
height_section_1 = 7.67
num_bends_section_1 = 2
num_bends_section_2 = 2


def main(start: float, stop: float, step: int):
    def q(vol_flow: float):
        output = []
        fermenter_in = {
            "volumetric_flow_in": vol_flow,
            "density_sugar": 1599,
            "density_ethanol": 789,
            "density_fiber": 1311,
            "density_water": 997,
        }
        fermenter_in["mass"] = fermenter_in["volumetric_flow_in"] * 1182

        for pump_name, pump_data in data["pumps"].items():
            if pump_name.find('(m)') != -1:
                continue

            x = pump_data["cost"][2]  # type: ignore
            pump_energy_loss_1 = fermenter_in["mass"] * g * height_section_1 / (3.6e6 * pump_data["coefficient"]) - fermenter_in["mass"] * g * height_section_1 / (3.6e6)  # type: ignore

            for bend_angle, bend_data in data["bends"].items():
                if bend_angle.find('(m)') != -1:
                    continue

                bend_energy_loss_1 = (
                    num_bends_section_1
                    * fermenter_in["mass"]
                    * 0.3
                    * (fermenter_in["volumetric_flow_in"] / 86400 / (pi * (pipe_radius_section_1**2))) ** 2
                    / (2 * g)
                ) / (3.6e6)

                for pipe_name, pipe_data in data["pipes"].items():
                    if pipe_name.find('(m)') != -1:
                        continue
                    for fermenter_name, fermenter_data in data["fermenters"].items():
                        fermenter_out = {
                            "fermenter_name": fermenter_name,
                            "volumetric_flow_in": fermenter_in["volumetric_flow_in"],
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
                        fermenter_out["volumetric_flow_out"] = fermenter_out["total_mass"] / fermenter_out["density"]
                        # print(fermenter_out)

                        bend_energy_loss_2 = (
                            num_bends_section_2
                            * fermenter_out["total_mass"]
                            * 0.3
                            * (fermenter_out["volumetric_flow_out"] / 86400 / (pi * (pipe_radius_section_2**2))) ** 2
                            / (2 * g)
                        ) / (3.6e6)

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
                            filter_out["volumetric_flow_out"] = filter_out["total_mass"] / filter_out["density"]

                            # print(filter_out)

                            for distiller_name, distiller_data in data["distillers"].items():
                                distiller_in = filter_out.copy()
                                distiller_out = distiller_in.copy()

                                divisor = (
                                    distiller_in["mass_water"] + distiller_in["mass_sugar"] + distiller_in["mass_fiber"]
                                )

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
                                distiller_out["volumetric_flow_out"] = (
                                    distiller_out["total_mass"] / distiller_out["density"]
                                )

                                # print(distiller_out)

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
                                    dehydrator_out["volumetric_flow_out"] = (
                                        dehydrator_out["total_mass"] / dehydrator_out["density"]
                                    )

                                    cost = fermenter_data["cost"] + filter_data["cost"] + distiller_data["cost"] + dehydrator_data["cost"]  # type: ignore
                                    dehydrator_out["cost"] = cost

                                    grade = dehydrator_out["mass_ethanol"] / dehydrator_out["total_mass"]
                                    if grade < 0.98:
                                        continue

                                    # velocity = (2 * 9.81 * (7.62 - 0)) ** 0.5

                                    output.append(
                                        {
                                            "Fermenter Out": fermenter_out,
                                            "Filter Out": filter_out,
                                            "Distiller Out": distiller_out,
                                            "Dehydrator Out": dehydrator_out,
                                            "Pump Energy Loss Section 1": pump_energy_loss_1,
                                            "Pump Efficiency": pump_data["coefficient"],
                                            "Bend Energy Loss Section 1": bend_energy_loss_1,
                                            "Bend Energy Loss Section 2": bend_energy_loss_2,
                                            "Mass Input": fermenter_in["mass"],
                                        }
                                    )
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
        return output

    x = {"data": q(1.2e6 / 264.17205)}
    with open("Volumetric Flow.json", "w", encoding='utf-8') as f:
        dump(x, f, indent=2)


if __name__ == '__main__':
    main(100, 5000, 100)
