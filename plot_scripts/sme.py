from rootsim_core.src.log.parse.rootsim_stats import RSStats

import os

import matplotlib.pyplot as plt

stats_names = {0: "time", 1: "memory", 2: "efficiency"}

mode_colors = {"PRECISE": (102/255, 1.0, 51/255),
               "AUTONOMIC": (51/255, 102/255, 1.0),
               "APPROXIMATED-0.25": (0.4, 117/255, 0),
               "APPROXIMATED-0.5": (0.6, 112/255, 0),
               "APPROXIMATED-0.75": (0.8, 107/255, 0),
               "APPROXIMATED-1.0": (1.0, 102/255, 0),
               "MANUAL-A": (204/255, 0, 102/255),
               "MANUAL-B": (102/255, 0, 204/255)}

mode_line_style = {
               "PRECISE": "solid",
               "AUTONOMIC": "dotted",
               "APPROXIMATED-0.25": (0, (4, 1)),
               "APPROXIMATED-0.5": (0, (3, 2)),
               "APPROXIMATED-0.75": (0, (2, 3)),
               "APPROXIMATED-1.0": (0, (1, 4)),
               "MANUAL-A": "dashdot",
               "MANUAL-B": "dashed"}


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
        if not filename.endswith(".bin") or "long" in filename or "agents-count" in filename:
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


def plot_draw(threads, data, data_label, figxs):
    figxs.set_xticks(threads)
    for mode, d in data.items():
        label = mode.lower().capitalize()
        figxs.plot(threads, d, marker='.', markersize=5, linewidth=1.5, label=label, color=mode_colors[mode],
                   markeredgecolor="midnightblue", markeredgewidth=0.1, linestyle=mode_line_style[mode])

    figxs.set_xlabel('# Worker threads')
    figxs.set_ylabel(data_label)
    figxs.grid(True)


def normalize_wrt_precise_percent(data):
    precise_data = list(data["PRECISE"])
    for mode, d in data.items():
        for i in range(len(d)):
            d[i] = precise_data[i] / d[i] * 100 - 100
    return data


def plot_model(model_name, threads, data):
    plt.clf()
    figsize = plt.figaspect(10/32)
    fig, figxs = plt.subplots(1, 3, figsize=figsize)

    memory_data = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == model_name and id_tup[1] == "memory"}
    for _, l in memory_data.items():  # convert in gigabytes
        for i in range(len(l)):
            l[i] /= 1024 * 1024 * 1024

    exec_time_data = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == model_name and id_tup[1] == "time"}
    eff_data = {id_tup[2]: d for id_tup, d in data.items() if id_tup[0] == model_name and id_tup[1] == "efficiency"}
    relative_exec_data = normalize_wrt_precise_percent(exec_time_data)

    plot_draw(threads, relative_exec_data, "Speedup w.r.t. precise mode (%)", figxs[0])
    plot_draw(threads, memory_data, "Memory usage (GB)", figxs[1])
    plot_draw(threads, eff_data, "Efficiency (%)", figxs[2])

    handles, labels = figxs[0].get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    fig.legend(handles, labels, bbox_to_anchor=(0, 1.0, 1, 0.0), loc='center', borderaxespad=0, ncol=5, frameon=False,
               fontsize="large")
    plt.savefig(f"plot_{model_name}.eps", dpi=300, bbox_inches='tight')


def speed_mem_eff_plot(dir_name):
    plt.rcParams['font.family'] = ['sans']
    plt.rcParams["axes.unicode_minus"] = False

    threads, data = load_rs_data(dir_name)

    plot_model("phold", threads, data)
    plot_model("tbc", threads, data)
