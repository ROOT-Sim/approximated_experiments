import json
import sys

from plot_scripts.stacked import stacked_plot
from plot_scripts.sme import speed_mem_eff_plot
from plot_scripts.agents_heatmap import agents_heatmap_thread_plot, agents_heatmap_plot, agent_heatmap_data_prepare
from plot_scripts.autonomic_heatmap import autonomic_heatmap_plot

experiments_config = {
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
    }
}


def load_configuration():
    with open("experiments_config.json", "r", encoding="utf8") as f:
        global experiments_config
        experiments_config = json.load(f)
    print("Experiments configuration successfully loaded")


if __name__ == "__main__":
    dir_name = sys.argv[1]
    load_configuration()
    tbc_long_threads = experiments_config["tbc-long"]["threads"]
    tbc_short_threads = experiments_config["tbc"]["threads"]
    stacked_plot(dir_name, max(tbc_long_threads), 1000)
    stacked_plot(dir_name, max(tbc_long_threads), 10000)
    stacked_plot(dir_name, min(tbc_long_threads), 1000)
    stacked_plot(dir_name, min(tbc_long_threads), 10000)
    speed_mem_eff_plot(dir_name)
    agent_heatmap_data_prepare(dir_name)
    agents_heatmap_plot()
    agents_heatmap_thread_plot(max(tbc_short_threads))
    agents_heatmap_thread_plot(min(tbc_short_threads))
    agents_heatmap_thread_plot(8)
    agents_heatmap_thread_plot(22)
    autonomic_heatmap_plot(dir_name, max(tbc_short_threads))
    autonomic_heatmap_plot(dir_name, tbc_short_threads[0])
