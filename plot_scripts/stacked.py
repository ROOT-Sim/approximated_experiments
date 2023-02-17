import os

import matplotlib.pyplot as plt

tbc_cats = ["Healthy", "Infected", "Sick", "Treatment", "Treated"]

LONG_RUN_MAX_VT = 10000
INTERVALS_COUNT = 1000


def fetch_data(dir_name, intervals, mode):
    n = 0
    aggregate = [[0 for _ in range(intervals)] for _ in range(5)]
    for filename in os.listdir(dir_name):
        if not filename.endswith("tbc_stats.txt") or filename.find(mode) == -1 or "long" not in filename:
            continue

        f = os.path.join(dir_name, filename)
        if not os.path.isfile(f):
            continue

        with open(f, "r") as f:
            for j, l in enumerate(f.readlines()):
                if j >= intervals:
                    break
                for i, v in enumerate(l.split()):
                    aggregate[i][j] += int(v)
        n += 1

    for l in aggregate:
        for i in range(len(l)):
            l[i] /= n * 1000000

    return aggregate


def stacked_plot(dir_name, threads, max_vt_to_show):
    if max_vt_to_show > LONG_RUN_MAX_VT:
        raise RuntimeError("vt is too high w.r.t. to our current experiment set")

    vt_per_interval = LONG_RUN_MAX_VT / INTERVALS_COUNT
    intervals = max_vt_to_show * INTERVALS_COUNT // LONG_RUN_MAX_VT

    xs = [vt_per_interval * i for i in range(intervals)]

    fig, axs = plt.subplots(4, 1)
    ax = axs[0]
    data = fetch_data(dir_name, intervals, "PRECISE")
    ax.set_xticklabels([])
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Precise", size="small")

    ax = axs[1]
    data = fetch_data(dir_name, intervals, f"{threads}_AUTONOMIC")
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.set_xticklabels([])
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Autonomic", size="small")

    ax = axs[2]
    data = fetch_data(dir_name, intervals, f"{threads}_MANUAL-A")
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.set_xticklabels([])
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Manual A", size="small")

    ax = axs[3]
    data = fetch_data(dir_name, intervals, f"{threads}_MANUAL-B")
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Manual B", size="small")

    fig.supylabel('Agents (in millions)', x=0.04)
    fig.supxlabel('Simulated day')

    handles, labels = axs[0].get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    fig.legend(handles, labels, bbox_to_anchor=(0, 0.95, 1.0, 0.0), loc='center', borderaxespad=0, ncol=5, frameon=False, fontsize="medium")
    plt.savefig(f"plot_{dir_name}_{threads}_{intervals}_tbc_evolution.eps", dpi=200, bbox_inches='tight')
