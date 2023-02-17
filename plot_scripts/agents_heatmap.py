import os

import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt

tbc_side_len = 128
INTERVALS_COUNT = 1000


def agent_heatmap_data_prepare(dir_name):
    data = np.zeros(tbc_side_len * tbc_side_len)
    n = 0
    for filename in os.listdir(dir_name):
        if not filename.endswith("_tbc_stats.txt") or "PRECISE" not in filename or "agents-count" not in filename:
            continue

        f = os.path.join(dir_name, filename)
        if not os.path.isfile(f):
            continue

        n += 1
        with open(f, "r") as f:
            for i, l in enumerate(f):
                if i >= tbc_side_len * tbc_side_len:
                    break
                n_agents = sum([int(v) for v in l.split()])
                data[i] += n_agents

    with open("full_tbc_stats.txt", "w") as f:
        for v in data:
            f.write(f"{v / (n * INTERVALS_COUNT)}\n")


def x_y_to_tid(i, j, threads):
    return (i * tbc_side_len + j) * threads // (tbc_side_len * tbc_side_len)


def load_data(threads=None):
    data = np.zeros((tbc_side_len, tbc_side_len))
    with open("full_tbc_stats.txt", "r") as f:
        for i, l in enumerate(f):
            data[i // tbc_side_len][i % tbc_side_len] = float(l)

    if threads is None:
        return data

    threads_data = [(0, 0) for _ in range(threads)]
    for i in range(tbc_side_len):
        for j in range(tbc_side_len):
            tid = x_y_to_tid(i, j, threads)
            tot, cnt = threads_data[tid]
            tot += data[i][j]
            cnt += 1
            threads_data[tid] = (tot, cnt)

    ret_data = [tot for tot, cnt in threads_data]

    for i in range(tbc_side_len):
        for j in range(tbc_side_len):
            tid = x_y_to_tid(i, j, threads)
            data[i][j] = ret_data[tid]

    return data


def agents_heatmap_thread_plot(threads):
    plt.rcParams['font.family'] = ['sans']
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots()
    data = load_data(threads)
    plt.gca().set_aspect('equal')
    ax.xaxis.set_ticks([0, tbc_side_len])
    ax.yaxis.set_ticks([0, tbc_side_len])
    ax.set_xlabel("x", labelpad=-10)
    ax.set_ylabel("y", rotation=0, labelpad=-15)
    print(f"With the currently computed agent distributions with {threads} threads we have "
          f"{100 * np.max(data) / np.min(data) - 100:3.1f}% max unbalance")

    vmin = round(np.min(data), -3)
    vmax = round(np.max(data), -3) + 1000
    im = ax.pcolormesh(data, cmap='copper_r', vmin=vmin, vmax=vmax, rasterized=True)
    cbar = fig.colorbar(im)
    cbar.set_ticks([vmin, vmax])
    cbar.set_label('Average number of agents handled by thread', rotation=270, labelpad=-23)

    for i in reversed(range(tbc_side_len)):
        for j in range(tbc_side_len):
            tid = x_y_to_tid(i, j, threads)
            tid_up = x_y_to_tid(i + 1, j, threads)
            tid_left = x_y_to_tid(i, j + 1, threads)
            if tid != tid_up and i + 1 != tbc_side_len:
                ax.add_line(
                    plt.Line2D((j, j + 1), (i + 1, i + 1), linewidth=0.3, color="maroon", solid_capstyle='butt'))

            if tid != tid_left and j + 1 != tbc_side_len:
                ax.add_line(
                    plt.Line2D((j + 1, j + 1), (i, i + 1), linewidth=0.3, color="maroon", solid_capstyle='butt'))

    plt.savefig(f"agents_partitioning_{threads}.eps", dpi=300, bbox_inches='tight')


def agents_heatmap_plot():
    plt.rcParams['font.family'] = ['sans']
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots()
    data = load_data()
    plt.gca().set_aspect('equal')
    ax.xaxis.set_ticks([0, tbc_side_len])
    ax.yaxis.set_ticks([0, tbc_side_len])
    ax.set_xlabel("x", labelpad=-10)
    ax.set_ylabel("y", rotation=0, labelpad=-15)
    im = ax.pcolormesh(data, cmap='copper_r', norm=mpl.colors.PowerNorm(3, vmin=50, vmax=100), linewidth=0,
                       rasterized=True)
    cbar = fig.colorbar(im)
    cbar.set_ticks([50, 100])
    cbar.set_label('Average number of agents', rotation=270, labelpad=-10)
    plt.savefig(f"average_agents.eps", dpi=300, bbox_inches='tight')
