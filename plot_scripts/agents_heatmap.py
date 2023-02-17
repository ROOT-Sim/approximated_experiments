import os

import numpy as np
from matplotlib import pyplot as plt

lps_dim = 128
rows_per_lp = 1000


def load_full_data(dir_name):
    data = np.zeros((lps_dim, lps_dim))
    n = 0
    for filename in os.listdir(dir_name):
        if not filename.startswith("tbc_stats_"):
            continue

        f = os.path.join(dir_name, filename)
        if not os.path.isfile(f):
            continue

        n += 1
        with open(f, "r") as f:
            for i, l in enumerate(f):
                n_agents = sum([int(v) for v in l.split()])
                lp_id = i // rows_per_lp
                data[lp_id // lps_dim][lp_id % lps_dim] += n_agents

    data = data / rows_per_lp
    data = data / n
    return data


def lpid_to_tid(lps, lp_id, threads):
    return lp_id * threads // lps


def load_data(threads):
    data = np.zeros((lps_dim, lps_dim))
    with open("full_tbc_stats.txt", "r") as f:
        for i, l in enumerate(f):
            data[i // lps_dim][i % lps_dim] = float(l)

    threads_data = [(0, 0) for _ in range(threads)]
    for i in range(lps_dim):
        for j in range(lps_dim):
            tid = lpid_to_tid(lps_dim * lps_dim, i * lps_dim + j, threads)
            tot, cnt = threads_data[tid]
            tot += data[i][j]
            cnt += 1
            threads_data[tid] = (tot, cnt)

    ret_data = [tot for tot, cnt in threads_data]

    for i in range(lps_dim):
        for j in range(lps_dim):
            tid = lpid_to_tid(lps_dim * lps_dim, i * lps_dim + j, threads)
            data[i][j] = ret_data[tid]

    return data


def agents_heatmap_thread_plot(threads):
    plt.rcParams['font.family'] = ['sans']
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots()
    data = load_data(threads)
    plt.gca().set_aspect('equal')
    ax.xaxis.set_ticks([0, 128])
    ax.yaxis.set_ticks([0, 128])
    ax.set_xlabel("x", labelpad=-10)
    ax.set_ylabel("y", rotation=0, labelpad=-15)
    print(np.min(data), np.max(data))
    vmin = round(np.min(data), -3)
    vmax = round(np.max(data), -3) + 1000
    im = ax.pcolormesh(data, cmap='copper_r', vmin=vmin, vmax=vmax, rasterized=True)
    cbar = fig.colorbar(im)
    cbar.set_ticks([vmin, vmax])
    cbar.set_label('Average number of agents handled by thread', rotation=270, labelpad=-23)

    for i in reversed(range(lps_dim)):
        for j in range(lps_dim):
            tid = lpid_to_tid(lps_dim * lps_dim, i * lps_dim + j, threads)
            tid_up = lpid_to_tid(lps_dim * lps_dim, (i + 1) * lps_dim + j, threads)
            tid_left = lpid_to_tid(lps_dim * lps_dim, i * lps_dim + j + 1, threads)
            if tid != tid_up and i + 1 != lps_dim:
                ax.add_line(
                    plt.Line2D((j, j + 1), (i + 1, i + 1), linewidth=0.3, color="maroon", solid_capstyle='butt'))

            if tid != tid_left and j + 1 != lps_dim:
                ax.add_line(
                    plt.Line2D((j + 1, j + 1), (i, i + 1), linewidth=0.3, color="maroon", solid_capstyle='butt'))

    plt.savefig(f"agents_partitioning_{threads}.eps", dpi=300, bbox_inches='tight')
