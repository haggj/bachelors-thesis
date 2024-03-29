"""
Helper functions that generate graphs of the generated data.
No tests are available for this file, since these functions simply creates output graphs.
"""
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter


def _label(rects, ax, as_int=True):
    """
    Attach a text label above each bar displaying its height
    """

    _, _, barlinecols = rects.errorbar

    for err_segment, rect in zip(barlinecols[0].get_segments(), rects):
        height = rect.get_height()
        if as_int and height >= 1:
            format_height = str(int(height))
        else:
            format_height = f'{height:.1f}'

        ax.text(rect.get_x() + rect.get_width() / 2,
                1.01 * err_segment[1][1],  # Use height of error bar as postition
                format_height,  # Use formatted height due to rect height
                ha='center', va='bottom')


def _plot_any(data, labels, file=None, title=None, y_axis="", log=False, as_int=True):
    # data = [
    #     {name:"sike generic",
    #     averages: [2,3,4,5],
    #     deviations: [0,0,0,0]},
    #     {name:"sike generic",
    #     averages: [2,3,4,5],
    #     deviations: [0,0,0,0]},
    #     {name:"sike generic",
    #     averages: [2,3,4,5],
    #     deviations: [0,0,0,0]},
    # ]
    # labels = ["keygena", "keygenb", "keygenc", "keygend"]

    number_of_implementations = len(data)

    x = np.arange(len(labels))
    width = 0.8 / number_of_implementations
    offset = -width * (number_of_implementations / 2)

    fig, ax = plt.subplots()

    count = 0

    for date in data:
        averages = date["values"]
        deviations = date.get("deviations")
        if deviations:
            rec = ax.bar(x + width * count + offset,
                         averages,
                         width,
                         label=date["name"],
                         yerr=deviations,
                         capsize=10)
        else:
            rec = ax.bar(x + width * count + offset,
                         averages,
                         width,
                         label=date["name"])
        _label(rec, ax, as_int)
        count += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    if title:
        ax.set_title(title)
    # Logarithmic y-axis
    if log:
        plt.yscale("log")
    plt.gca().yaxis.set_major_formatter(ScalarFormatter())
    ax.set_ylabel(y_axis)
    # X-axis
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    # Legend
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
              fancybox=True, ncol=5)
    # size
    fig.set_size_inches(20, 10)

    # Save as file
    if file:
        Path("data").mkdir(parents=True, exist_ok=True)
        fig.savefig('data/' + file + '.png', dpi=100, bbox_inches='tight')


def _map_to_ecdh(curve):
    if curve == "434":
        return "secp256"
    if curve == "610":
        return "secp384"
    if curve == "751":
        return "secp521"
    return None


def _generate(result, implementations):
    font = {'size': 18}
    matplotlib.rc('font', **font)
    plt.rcParams['axes.prop_cycle'] = plt.cycler(
        color=['#F9C74F', '#577590', '#F94144', '#43AA8B', '#F3722C', '#90BE6D'])
    plt.rcParams['axes.prop_cycle'] = plt.cycler(
        color=['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#ffdd00'])
    plt.rcParams['axes.prop_cycle'] = plt.cycler(
        color=['#1F77B4', '#F49500', '#009B5B', '#EC0000', '#fff94c', '#79008D', '#72D200'])

    curves = ["434", "503", "610", "751"]
    for curve in curves:
        # 1. Collect all benchmarks of specific curve
        data_instructions = []
        data_memory = []
        for name in implementations:
            impl = result.get(name)
            if not impl:
                continue
            found = impl.get_curve_by_name(_map_to_ecdh(curve) if impl.name == "ECDH" else curve)
            if not found:
                continue
            # implementation has benchmarks for specifc curve -> add

            # Add instruction benchmarks
            values, deviations = found.get_benchmarks_for_plot()
            dic = {
                "name": impl.name + ("(Reference Value)" if impl.name == "ECDH" else ""),
                "values": values,
                "deviations": deviations,
            }
            data_instructions.append(dic)

            # Add memory benchmarks
            values = [round(found.benchmark_average("Memory") / 1000, 1)]
            deviations = [round(found.benchmark_stdev("Memory") / 1000, 1)]
            dic = {
                "name": impl.name + ("(Reference Value)" if impl.name == "ECDH" else ""),
                "values": values,
                "deviations": deviations,
            }
            data_memory.append(dic)

        # 2. Generate graph for all benchmarks of specific curve
        _plot_any(data=data_instructions,
                 labels=['Keygen A', 'Keygen B', 'Secret A', 'Secret B'],
                 log=True,
                 as_int=True,
                 file=str(curve),
                 y_axis="Overall Instructions in 1.000.000\n")

        _plot_any(data=data_memory,
                 labels=[''],
                 log=False,
                 as_int=False,
                 file=str(curve) + "_mem",
                 y_axis="Memory in Kilobytes")


def generate_graph_for(implementation, ecdh=None):
    # Generates graphs for a single implementation (includes parameters are listed within on graph)
    # Both parameters are objects of type BenchmarkImpl

    data_instructions = []
    data_memory = []
    name = implementation.name

    curves = ["434", "503", "610", "751"]
    for curve in curves:
        found = implementation.get_curve_by_name(curve)
        if not found:
            continue
        # Instructions
        values, deviations = found.get_benchmarks_for_plot()
        dic = {
            "name": name + " p" + curve,
            "values": values,
            "deviations": deviations,
        }
        data_instructions.append(dic)

        # Memory
        values = [round(found.benchmark_average("Memory") / 1000, 1)]
        deviations = [round(found.benchmark_stdev("Memory") / 1000, 1)]
        dic = {
            "name": name + " p" + curve,
            "values": values,
            "deviations": deviations,
        }
        data_memory.append(dic)

    if ecdh:
        for curve in ecdh.curves:
            if name == "CIRCL_x64" and curve.name == "secp384":
                continue
            values, deviations = curve.get_benchmarks_for_plot()
            data_instructions.append(
                {
                    "name": "ECDH " + curve.name,
                    "values": values,
                    "deviations": deviations,
                }

            )
            data_memory.append(
                {
                    "name": "ECDH " + curve.name,
                    "values": [round(curve.benchmark_average("Memory") / 1000, 1)],
                    "deviations": [round(curve.benchmark_stdev("Memory") / 1000, 1)],
                }
            )

    _plot_any(data=data_instructions,
             labels=['Keygen A', 'Keygen B', 'Secret A', 'Secret B'],
             log=False,
             file=name,
             y_axis="Overall Instructions in 1.000.000\n")

    _plot_any(data=data_memory,
             labels=[''],
             log=False,
             as_int=False,
             file=name + "_mem",
             y_axis="Memory in Kilobytes")


def generate_graphs(result):
    """
    This function generates graphs based on the measured benchmarking data. Modify the list implementations below to
    determine if an implementation is included into the output graph.
    By default multiple graphs (one for each available curve) are generated. Additionally a separate graph for
    1) counted instructions and 2) allocated memory will be part of the output. To create more individual graphs refer
    to the called subroutines _generate() and _plot_any() in this file.

    Args:
        result (dict): Results from the benchmarking suite

    Returns:
        Saves the output graphs in an intermediate folder within the docker container. Once the suite ran successfully,
        you can access these graphs in the data/ subfolder of your current directory.
    """

    # Do not include more than 6 implementations to obtain nice graphs
    implementations = [
        # SIKE
        # "Sike_Reference",
        "Sike_Generic",
        # "Sike_Generic_Compressed",
        "Sike_x64",
        # "Sike_x64_Compressed",

        # MICROSOFT
        # Microsoft_Generic",
        # "Microsoft_Generic_Compressed",
        # "Microsoft_x64",
        # "Microsoft_x64_Compressed",

        # CIRCL
        "CIRCL_Generic",
        "CIRCL_x64",

        # ECDH
        "ECDH",
    ]
    _generate(result, implementations)


