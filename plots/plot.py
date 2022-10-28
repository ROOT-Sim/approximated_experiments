import os
import sys

import matplotlib.pyplot as plt

from rootsim_core.src.log.parse.rootsim_stats import RSStats

stats_names = {0: "time", 1: "memory", 2: "efficiency"}


def load_rs_stats_file(file_name):
    rs_stats = RSStats(file_name)
    processed_msgs = rs_stats.thread_metric_get("processed messages", aggregate_nodes=True, aggregate_gvts=True)
    rollback_msgs = rs_stats.thread_metric_get("rolled back messages", aggregate_nodes=True, aggregate_gvts=True)
    memory = rs_stats.nodes_stats["maximum_resident_set"][0]

    efficiency = 100 * (processed_msgs - rollback_msgs) / processed_msgs if processed_msgs else 100

    return int(sum(rs_stats.threads_count)), rs_stats.nodes_stats["processing_time"][0] / 1000000, memory, efficiency


def load_rs_data(dir_name):
    data = {}
    threads_counts = set()
    stats_count = 0
    for filename in os.listdir(dir_name):
        if not filename.endswith(".bin"):
            continue

        f = os.path.join(dir_name, filename)
        if not os.path.isfile(f):
            continue

        threads, *stats = load_rs_stats_file(f)
        threads = int(threads)
        stats_count = max(len(stats), stats_count)
        model_name = filename.split("_")[0]
        approx_mode = filename.split("_")[3]
        if model_name not in data:
            data[model_name] = {}
        if approx_mode not in data[model_name]:
            data[model_name][approx_mode] = {}
        if threads not in data[model_name][approx_mode]:
            threads_counts.add(threads)
            data[model_name][approx_mode][threads] = []

        data[model_name][approx_mode][threads].append(stats)

    threads_counts = sorted(list(threads_counts))
    threads_map = {t: p for p, t in enumerate(threads_counts)}

    final_data = {}
    for model_name, model_data in data.items():
        for approx_mode, mode_data in model_data.items():
            for threads, threads_data in mode_data.items():
                aggr_stats = [0 for _ in range(stats_count)]
                for tup in threads_data:
                    for i, v in enumerate(tup):
                        aggr_stats[i] += v

                for i in range(stats_count):
                    id_tup = (model_name, stats_names[i], approx_mode)
                    if id_tup not in final_data:
                        final_data[id_tup] = [0 for _ in threads_counts]
                    final_data[id_tup][threads_map[threads]] = aggr_stats[i] / len(threads_data)

    return threads_counts, final_data


def plot_draw(threads, data, data_label, title):
    plt.clf()
    fig, figxs = plt.subplots()
    figxs.set_xticks(threads)
    for mode, d in data.items():
        figxs.plot(threads, d, marker='.', markersize=3, label=mode)
    figxs.set_xlabel('Threads')
    figxs.set_ylabel(data_label)
    figxs.set_title(title)
    figxs.set_ylim(bottom=0)
    figxs.label_outer()
    figxs.grid(True)
    handles, labels = figxs.get_legend_handles_labels()
    # sort both labels and handles by labels
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    figxs.legend(handles, labels)
    plt.savefig(f"plot_{title.replace(' ', '_')}.png", dpi=100)


def convert_to_relative_to_precise(data):
    precise_data = data["PRECISE"]
    del data["PRECISE"]
    for mode, d in data.items():
        for i, dd in enumerate(zip(d, precise_data)):
            d[i] = dd[1]/dd[0]
    return data


def plot(dir_name):
    plt.rcParams['font.family'] = ['monospace']
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["image.cmap"] = "Set2"
    plt.rcParams['axes.prop_cycle'] = plt.cycler(color=plt.cm.Set2.colors)

    threads, data = load_rs_data(dir_name)
    data_phold_memory = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == "phold" and id_tup[1] == "memory"}
    data_tbc_memory = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == "tbc" and id_tup[1] == "memory"}
    data_phold_exec = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == "phold" and id_tup[1] == "time"}
    data_tbc_exec = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == "tbc" and id_tup[1] == "time"}
    data_phold_eff = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == "phold" and id_tup[1] == "efficiency"}
    data_tbc_eff = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == "tbc" and id_tup[1] == "efficiency"}

    plot_draw(threads, data_phold_memory, "Memory", "PHOLD memory usage")
    plot_draw(threads, data_phold_exec, "Time", "PHOLD execution time")
    plot_draw(threads, data_phold_eff, "Efficiency", "PHOLD efficiency")
    plot_draw(threads, data_tbc_memory, "Memory", "TBC memory usage")
    plot_draw(threads, data_tbc_exec, "Time", "TBC execution time")
    plot_draw(threads, data_tbc_eff, "Efficiency", "TBC efficiency")


if __name__ == "__main__":
    plot(sys.argv[1])
