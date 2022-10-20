#!/usr/bin/env python3
import os
from datetime import datetime

from plots.plot import plot

values_interations = range(3)
values_threads = [16, 12, 8, 4, 1]
values_mode = ["PRECISE", "APPROXIMATED", "AUTONOMIC"]
values_phold_lps = [1024]
values_phold_percentage = [0.0, 0.25, 0.5, 0.75, 1.0]


def prepare_rootsim():
    if os.path.exists("rootsim_core_build"):
        return

    os.system("rm -r rootsim_core_build_tmp")
    res = os.system("cmake -S rootsim_core -B rootsim_core_build_tmp -DCMAKE_BUILD_TYPE=RELEASE")

    if os.waitstatus_to_exitcode(res) != 0:
        print("cmake configure failed!")
        exit(-1)

    res = os.system("cmake --build rootsim_core_build_tmp")

    if os.waitstatus_to_exitcode(res) != 0:
        print("cmake configure failed!")
        exit(-1)

    os.system("rm -r rootsim_core_build")
    os.system("mv rootsim_core_build_tmp rootsim_core_build")


def write_config(num_lps, num_threads, mode, percentage=1.0):
    with open("config.h", "w") as f:
        f.write("#pragma once\n\n")
        f.write(f"#define NUM_THREADS {num_threads}\n")
        f.write(f"#define EXEC_MODE APPROXIMATED_MODE_{mode}\n")
        f.write(f"#define NUM_LPS {num_lps}\n")
        f.write(f"#define APPROXIMATED_PERCENTAGE {percentage}\n")


def rootsir_run(param_str, model_folder, collect_tbc=False):
    print(f"Running rootsim_{param_str}")

    # Check if this conf has already run
    if os.path.exists(f"data/{model_folder}_{param_str}.bin"):
        print(f"rootsim_{param_str} already run")
        return

    os.system(f"mpicc -O3 ./{model_folder}/*.c ./rootsim_core_build/src/librscore.a -I. -Irootsim_core/src -lm -pthread -o model")
    os.system("rm -f root_sir_stats.bin")

    a = datetime.now()
    os.system(f"./model")
    t = (datetime.now() - a).total_seconds()
    with open("data/times.txt", "a") as f:
        spaced_str = param_str.replace('_', '\t')
        f.write(f"{model_folder}\t{spaced_str}\t{t}\n")

    if collect_tbc:
        os.system(f"mv tbc_stats.txt data/{model_folder}_{param_str}_tbc_stats.txt")
    else:
        os.system("rm -f tbc_stats.txt")
    os.system(f"mv root_sir_stats_phases.txt data/{model_folder}_{param_str}_phases.txt")
    os.system(f"mv root_sir_stats.bin data/{model_folder}_{param_str}.bin")
    return


# Collect data for all configurations and model versions
def collect_phold_data():
    os.system("mkdir -p data")
    for iteration in values_interations:
        for num_threads in values_threads:
            for num_lps in values_phold_lps:
                for mode in values_mode:
                    for percentage in values_phold_percentage:
                        if mode == "PRECISE":
                            param_str = f"{num_lps}_{num_threads}_{mode}_{iteration}"
                        else:
                            param_str = f"{num_lps}_{num_threads}_{mode}-{percentage}_{iteration}"
                        write_config(num_lps, num_threads, mode, percentage)
                        rootsir_run(param_str, "phold")


def collect_tbc_data():
    os.system("mkdir -p data")
    for iteration in values_interations:
        for num_threads in values_threads:
            for mode in values_mode:
                num_lps = 16384
                param_str = f"{num_lps}_{num_threads}_{mode}_{iteration}"
                write_config(num_lps, num_threads, mode)
                rootsir_run(param_str, "tbc", collect_tbc=True)


prepare_rootsim()
collect_phold_data()
collect_tbc_data()
plot("data")
