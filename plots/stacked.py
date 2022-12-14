import os

import matplotlib.pyplot as plt

tbc_cats = ["Healthy", "Infected", "Sick", "Treatment", "Treated"]
intervals = 2000
vt_per_interval = 5


def fetch_data(dir_name, type="PRECISE"):
    n = 0
    aggregate = [[0 for _ in range(intervals)] for _ in range(5)]
    for filename in os.listdir(dir_name):
        if not filename.endswith("tbc_stats.txt") or not filename.startswith(f"tbc_16384_") or filename.find(type) == -1:
            continue

        f = os.path.join(dir_name, filename)
        if not os.path.isfile(f):
            continue

        with open(f, "r") as f:
            for j, l in enumerate(f.readlines()):
                for i, v in enumerate(l.split()):
                    aggregate[i][j] += int(v)
        n += 1

    for l in aggregate:
        for i in range(len(l)):
            l[i] /= n * 1000000

    return aggregate


def do_plot(dir_name, threads):
    xs = [vt_per_interval * i for i in range(intervals)]

    fig, axs = plt.subplots(5, 1)
    ax = axs[0]
    data = fetch_data(dir_name)
    ax.set_xticklabels([])
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Precise")

    ax = axs[1]
    data = fetch_data(dir_name, f"{threads}_APPROXIMATED")
    ax.set_xticklabels([])
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Approximated")

    ax = axs[2]
    data = fetch_data(dir_name, f"{threads}_AUTONOMIC")
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.set_xticklabels([])
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Autonomic")

    ax = axs[3]
    data = fetch_data(dir_name, f"{threads}_MANUAL")
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.set_xticklabels([])
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Manual")

    ax = axs[4]
    data = fetch_data(dir_name, f"{threads}_MANUALINV")
    ax.stackplot(xs, data, labels=tbc_cats)
    ax.yaxis.set_label_position("right")
    ax.set_ylabel("Inv Manual")

    fig.supylabel('Agents (in millions)', x=0.04)
    fig.supxlabel('Simulated day')

    handles, labels = axs[0].get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    fig.legend(handles, labels, bbox_to_anchor=(0, 0.95, 1.0, 0.0), loc='center', borderaxespad=0, ncol=5, frameon=False, fontsize="medium")
    plt.savefig(f"plot_{dir_name}_{threads}_paa.eps", dpi=200, bbox_inches='tight')

