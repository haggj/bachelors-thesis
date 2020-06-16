import msparser
import gprof2dot
import subprocess
import pandas


from statistics import mean
from prettytable import PrettyTable

def bash(command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    stream = process.communicate()
    return_code = process.returncode
    if return_code != 0:
        print ("Error during command: " + command)
        print(stream)
        exit(0)
    return

def getCallgrindFunctionCalls(callgrind, function):
    """Opens a callgrind.out file and returns all functions called within the specified function.

    Args:
        callgrind (path): Path to callgrind file
        function (string): Name of a called function

    Returns:
       dict: dictionary that contains all called function with the specified function as keys (values are the measured opcounts)
    """
    f = open(callgrind)
    parser = gprof2dot.CallgrindParser(f)
    profile = parser.parse()

    ret = {}

    for call in profile.functions[function].calls.values():
        callee = profile.functions[call.callee_id]

        for event, data in call.events.items():
            if event.name == "Samples":
                ret[callee.name] = int(data)
    return ret

def print_statistics(result):
    #result is list of dictionaries
    TABLE = PrettyTable()
    TABLE.field_names = list(result[0].keys())

    for r in result:
        TABLE.add_row(list(r.values()))

    print(TABLE)


class Base_Implementation():

    def __init__(self):
        self.path = ""

    def map_functions(self, callgrind_result):
        res = {
            "PrivateKeyA": 0,
            "PublicKeyA": 0 ,
            "PrivateKeyB": 0,
            "PublicKeyB": 0,
            "SecretA": 0,
            "SecretB": 0
        }
        raise NotImplementedError("Mapping not implemented")

    def callgrind_result(self):
        calls = getCallgrindFunctionCalls(self.path+"/benchmarks/callgrind.out", "benchmark_keygen")
        return self.map_functions(calls)

    def callgrind_average(self, count):
        results = []
        for i in range(count):
            bash('make callgrind -C {}'.format(self.path))
            res = self.callgrind_result()
            results.append(res)
            print ("callgrind: " + str(i), end="\r")

        df = pandas.DataFrame(results)
        average = dict(df.mean())
        return average

    def massif_result(self):
        data = msparser.parse_file(self.path+"/benchmarks/massif.out")
        peak =  data["peak_snapshot_index"]
        peak_data = data["snapshots"][peak]
        peak_mem = int(peak_data["mem_heap"]) + int(peak_data["mem_heap_extra"]) + int(peak_data ["mem_stack"])
        return peak_mem


    def massif_average(self, count):
        results = []
        for i in range(count):
            bash('make massif -C {}'.format(self.path))
            res = self.massif_result()
            results.append(res)
            print ("massif: " + str(i), end="\r")
        return int(mean(results))


    def get_statistics(self, count, args):
        #compile and generate benchmark outputs  
        bash('make build -B -C {} {}'.format(self.path, args))

        result = self.callgrind_average(count)
        result["Memory"] = self.massif_average(count)

        return {k:format(int(v), ",").replace(",", ".") for k, v in result.items()}
