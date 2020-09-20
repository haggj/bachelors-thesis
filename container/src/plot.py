
from prettytable import PrettyTable
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Process
from pathlib import Path
import json
import os
from src.base import bcolors

def autolabel(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

map_float = lambda x: float(x.replace(".", ""))
map_round = lambda x: round(float(x)/1000000,1)

def plotCurve(result, name, memory=False):
    
    labels = []
    if not memory:
        labels = ['Keygen A', 'Keygen B', 'Secret A', 'Secret B']
        if "ECDH" in result:
            ecdh_means = list(map(map_float, list(result["ECDH"][0].values())[2:-1]))
            ecdh_means = list(map(map_round, ecdh_means))
        title = 'Overall Instructions for Parameters '
        y_axis = 'Overall Instructions in 1.000.000'
    else:
        labels = ["Memory"]
        if "ECDH" in result:
            ecdh_means = float(list(result["ECDH"][0].values())[-1])
            ecdh_means = round(ecdh_means,1)
        title = 'Maximum memory consumption in kilobytes for '
        y_axis = 'Memory in Kilobytes'



    x = np.arange(len(labels)) # the label locations
    margin = 0.25
    width = (1.-2.*margin)/(1 if memory else 4)

    offset = -width*3

    fig, ax = plt.subplots()

    if "ECDH" in result:
        ecdh = ax.bar(x + offset, ecdh_means, width, label='ECDH (Reference value)')
        autolabel(ecdh, ax)

    count = 1

    for implementation, list_of_results in result.items():
        #Ignored implementations in graph
        if implementation in ["Sike Reference", "Sike Optimized", "Sike Optimized Compressed"]:
            continue
        for curve in list_of_results:
            if name == curve['Curve']:
                if not memory:
                   
                    stats = list(map(map_float, list(curve.values())[2:-1]))
                    keygen_a =stats[0] + stats[1]
                    keygen_b = stats[2] + stats[3]
                    mean = [keygen_a, keygen_b, stats[4], stats[5]]
                    mean = list(map(map_round, mean))
                    rec = ax.bar(x + width*count + offset, mean, width, label=implementation)
                else:
                    mean = list(curve.values())[-1]
                    mean = [round(int(mean.replace(".", ""))/1000,1)]
                    rec = ax.bar(x + width*count + offset, mean, width, label=implementation)

                
                autolabel(rec, ax)
                count += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel(y_axis)
    ax.set_title(title + name)
    ax.set_xticks(x)
    ax.set_xticklabels([] if memory else labels)
    ax.legend()
    ax.set_ylim(bottom=0)
    fig.set_size_inches(18, 8)

    Path("data").mkdir(parents=True, exist_ok=True)
    if not memory:
        fig.savefig('data/' + name +'.png', dpi=100)
    else:
        fig.savefig('data/' + name + '_mem.png', dpi=100)


def generatePlot(result):
    curves = ["p434", "p503" , "p610", "p751"]
    processes = []
    for curve in curves:
        r = result
        #Generates plots regarding instructions
        p1 = Process(target=plotCurve, args=(r, curve, False))
        p1.start()
        #Generates plots regarding memory
        p2 = Process(target=plotCurve, args=(r, curve, True))
        p2.start()
        processes.append(p1)
        processes.append(p2)
    
    for p in processes:
        p.join()

def generateTable(results):
    with open('pre.html', "r") as file:
        preHTML = file.read()

    Path("data").mkdir(parents=True, exist_ok=True)
    with open('data/result.html','w') as file:
        file.write(preHTML + "<p>All values (except memory) are absolute instruction counts.</p><p>*Maximum memory consumption in bytes.</p>")
        for key, value in results.items():
            file.write("<h1>" + key + "</h1>")
            file.write(format_statstics(value).replace("Memory", "Memory*"))
        file.write("</body></html>")
    
def format_statstics(result):
    #result is instance of class BenchmarkImpl
    TABLE = PrettyTable()
    TABLE.field_names = result.get_benchmark_names()

    for curve in result.curves:
        TABLE.add_row(curve.get_benchmark_values())

    return TABLE.get_html_string()

def saveAsJson(result):
    if os.path.isfile("cached.json"):
        with open('data/cached.json', 'a') as f:
            json.dump(result, f)
    else:
         with open('data/cached.json', 'w+') as f:
            json.dump(result, f)

def loadFromJson():
    if os.path.isfile("data/cached.json"):
        with open('data/cached.json', 'r') as f:
            cached = json.load(f)
            print("\nUsing cached data for:\n" + bcolors.WARNING + "\t\n".join(cached.keys())  + bcolors.ENDC)
            return cached
    return {}