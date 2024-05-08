import subprocess
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def run_competition_script(times, param):
    for _ in range(times):
        command = ["python", "competition.py"] + param
        subprocess.run(command)


params = ["--time-budget", "120", "--executor", "dave2", "--map-size", "400",
          "--module-name", "sample_test_generators.module", "--class-name",
          "class"]

module_name = ["random_generator", "hc_generator", "sa_generator", "ts_generator", "ga_generator"]
class_name = ["RandomTestGenerator", "HC", "SA", "TS", "GA"]

if __name__ == '__main__':
    for i in range(5):
        params[-3] = params[-3].split('.')[0] + '.' + module_name[i]
        params[-1] = class_name[i]
        run_competition_script(1, params)
