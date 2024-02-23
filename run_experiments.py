#!/usr/bin/env python3
import json
import os
from datetime import datetime

phold_lps = 1024
phold_approximated_percentages = [0.25, 0.5, 0.75, 1.0]

tbc_lps = 16384
tbc_modes = ["PRECISE", "AUTONOMIC", "MANUAL-A", "MANUAL-B"]

pcs_lps = [256, 1024, 4096]

experiments_config = {
    "base": {
        "threads": [],
        "repetitions": 0
    },
   "phold": {
       "threads": [],
       "repetitions": 0
   },
   "tbc": {
       "threads": [],
       "repetitions": 0
   },
   "tbc-long": {
       "threads": [],
       "repetitions": 0
   },
   "tbc-agents-count": {
       "threads": 0,
       "repetitions": 0
   }
}


def load_configuration():
    with open("experiments_config.json", "r", encoding="utf8") as f:
        global experiments_config
        experiments_config = json.load(f)
    print("Experiments configuration successfully loaded")


def prepare_rootsim():
    if os.path.exists("rootsim_core_build"):
        print("ROOT-Sim is already built; if you want to rebuild it, delete the folder named 'rootsim_core_build'")
        return

    os.system("rm -r rootsim_core_build_tmp")
    res = os.system("cmake -S rootsim_core -B rootsim_core_build_tmp -DCMAKE_BUILD_TYPE=RELEASE -DDISABLE_MPI=YES")

    if os.waitstatus_to_exitcode(res) != 0:
        print("cmake configure failed!")
        exit(-1)

    res = os.system("cmake --build rootsim_core_build_tmp")

    if os.waitstatus_to_exitcode(res) != 0:
        print("cmake configure failed!")
        exit(-1)

    os.system("rm -r rootsim_core_build")
    os.system("mv rootsim_core_build_tmp rootsim_core_build")
    print("ROOT-Sim successfully built")

def write_config_base(num_lps, num_threads, vals, mode):
    with open("config.h", "w") as f:
        f.write("#pragma once\n\n")
        f.write(f"#define NUM_THREADS {num_threads}\n")
        f.write(f"#define EXEC_MODE APPROXIMATED_MODE_PRECISE\n")
        f.write(f"#define NUM_LPS {num_lps}\n")
        f.write(f"#define SMART_RESTORE {mode}\n")
        f.write(f"#define RANGE {vals}\n")

def write_config(num_lps, num_threads, mode, percentage=1.0, tbc_long=False, tbc_agents_count=False, pcs_gvt=0, pcs_calls=0):
    with open("config.h", "w") as f:
        f.write("#pragma once\n\n")
        f.write(f"#define NUM_THREADS {num_threads}\n")
        f.write(f"#define EXEC_MODE APPROXIMATED_MODE_{mode}\n")
        f.write(f"#define NUM_LPS {num_lps}\n")
        f.write(f"#define APPROXIMATED_PERCENTAGE {percentage}\n")
        if tbc_agents_count:
            f.write("#define TBC_FULL_COUNT\n")
        if tbc_long:
            f.write("#define TBC_LONG_RUN\n")
        if mode == "MANUAL-A":
            f.write(f"#define MANUAL_MODE 1\n")
        elif mode == "MANUAL-B":
            f.write(f"#define MANUAL_MODE 2\n")
        if pcs_gvt != 0:
            f.write(f"#define PCS_END_GVT {pcs_gvt}\n")
        if pcs_calls != 0:
            f.write(f"#define PCS_ENDS_CALL {pcs_calls}\n")
        


def rootsir_run(param_str, model_folder, collect_tbc=False):
    model_str = f"{model_folder}_{param_str}"
    print(f"Running {model_str}")

    # Check if this conf has already run
    if os.path.exists(f"data/{model_str}.bin"):
        print(f"{model_str} already run")
        return

    os.system(f"gcc -O3 -Wno-incompatible-pointer-types ./{model_folder}/*.c ./rootsim_core_build/src/librscore.a -I. "
              f"-Irootsim_core/src -lm -pthread -o model")
    os.system("rm -f root_sir_stats.bin")

    a = datetime.now()
    os.system(f"./model > {model_str}_evo.txt")
    t = (datetime.now() - a).total_seconds()
    with open("data/times.txt", "a") as f:
        spaced_str = model_str.replace('_', '\t')
        f.write(f"{spaced_str}\t{t}\n")

    if collect_tbc:
        os.system(f"mv tbc_stats.txt data/{model_str}_tbc_stats.txt")
    else:
        os.system("rm -f tbc_stats.txt")
    os.system(f"mv root_sir_stats_phases.txt data/{model_str}_phases.txt")
    os.system(f"mv root_sir_stats.bin data/{model_str}.bin")
    os.system(f"python3 rootsim_core/src/log/parse/rootsim_stats.py data/{model_str}.bin")
    os.system(f"mv *.txt data/")


# Collect data for all configurations and model versions
def collect_data(test):
    lps=[320, 640] #[10, 20, 40, 80, 160, 320, 640]
    if "pcs" in test:
        lps = pcs_lps
    os.system("mkdir -p data")
    for lp in lps:
        for iteration in range(experiments_config[test]["repetitions"]):
            for num_threads in experiments_config[test]["threads"]:
                for m in ["BOUNDED"]:
                    #for r in ["RANGE_1_1pC", "RANGE_0_1", "RANGE_1_1pI", "RANGE_0_1pI"]:
                    for r in ["RANGE_0_1pI"]:
                        write_config_base(lp, num_threads, r, m)
                        param_str = f"{m}_{r}_{lp}_{num_threads}_{iteration}"
                        rootsir_run(param_str, test)
                        #os.system(f"python3 process-abs.py {model_str}")
                        if "pcs" not in test:
                            model_str = f"data/{test}_{param_str}_evo.txt"
                            os.system(f"python3 process-rel.py {model_str}")
    print(f"{test} experiments completed")

# Collect data for all configurations and model versions
def collect_data_pcs():
    lps = pcs_lps
    test="pcs"
    r = "RANGE_0_1pI" 
    os.system("mkdir -p data")
    for lp in lps:
        for iteration in range(experiments_config[test]["repetitions"]):
            for num_threads in experiments_config[test]["threads"]:
                for m in range(2):
                    write_config_base(lp, num_threads, r, m, 1500, 0)
                    param_str = f"{m}_{r}_{lp}_{num_threads}_{iteration}"
                    rootsir_run(param_str, test)
    print(f"{test} experiments completed")

def collect_phold_data():
    os.system("mkdir -p data")
    for iteration in range(experiments_config["phold"]["repetitions"]):
        for num_threads in experiments_config["phold"]["threads"]:
            write_config(phold_lps, num_threads, "PRECISE")
            param_str = f"{phold_lps}_{num_threads}_PRECISE_{iteration}"
            rootsir_run(param_str, "phold")
            for percentage in phold_approximated_percentages:
                write_config(phold_lps, num_threads, "APPROXIMATED", percentage)
                param_str = f"{phold_lps}_{num_threads}_APPROXIMATED-{percentage}_{iteration}"
                rootsir_run(param_str, "phold")
    print("PHOLD experiments completed")


def collect_tbc_data():
    os.system("mkdir -p data")
    for iteration in range(experiments_config["tbc"]["repetitions"]):
        for num_threads in experiments_config["tbc"]["threads"]:
            for mode in tbc_modes:
                write_config(tbc_lps, num_threads, mode)
                param_str = f"{tbc_lps}_{num_threads}_{mode}_{iteration}"
                rootsir_run(param_str, "tbc", collect_tbc=True)
    print("TBC experiments completed")


def collect_tbc_agents_count_data():
    os.system("mkdir -p data")
    num_threads = experiments_config["tbc-agents-count"]["threads"]
    for iteration in range(experiments_config["tbc-agents-count"]["repetitions"]):
        write_config(tbc_lps, num_threads, "PRECISE", tbc_agents_count=True)
        param_str = f"{tbc_lps}-agents-count_{num_threads}_PRECISE_{iteration}"
        rootsir_run(param_str, "tbc", collect_tbc=True)
    print("TBC-agents-count experiments completed")


def collect_tbc_long_data():
    os.system("mkdir -p data")
    for iteration in range(experiments_config["tbc-long"]["repetitions"]):
        for num_threads in experiments_config["tbc-long"]["threads"]:
            for mode in tbc_modes:
                write_config(tbc_lps, num_threads, mode, tbc_long=True)
                param_str = f"{tbc_lps}-long_{num_threads}_{mode}_{iteration}"
                rootsir_run(param_str, "tbc", collect_tbc=True)
    print("TBC-long experiments completed")


load_configuration()
prepare_rootsim()
#collect_data("base_v02")
collect_data_pcs()
#collect_data("incr")
#collect_phold_data()
#collect_tbc_data()
#collect_tbc_agents_count_data()
#collect_tbc_long_data()
print("Experiments completed!")
