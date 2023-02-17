import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from rootsim_core.src.log.parse.rootsim_stats import RSStats

lps_dim = 128
square_width = 5


def load_rs_stats_file(file_name, get_gvts=False):
    rs_stats = RSStats(file_name)
    if get_gvts:
        return len(rs_stats.gvts)

    return rs_stats.thread_metric_get("rolled back messages", aggregate_gvts=True)[0]


def get_precise_thread_load(dir_name, threads):
    data = np.zeros(threads, dtype=float)

    n = 0
    for filename in os.listdir(dir_name):
        if not filename.endswith(".bin") or not filename.startswith(f"tbc_16384_{threads}_AUTONOMIC"):
            continue

        f = os.path.join(dir_name, filename)
        if not os.path.isfile(f):
            continue

        procs = load_rs_stats_file(f)
        for i, v in enumerate(procs):
            data[i] += v

        n += 1

    for i in range(threads):
        data[i] /= n

    return data


def lpid_to_tid(lps, lp_id, threads):
    return lp_id * threads // lps


def get_gvts_count(dir_name, threads):
    n = 0
    gvts = 0
    for filename in os.listdir(dir_name):
        if not filename.endswith(".bin") or not filename.startswith(f"tbc_16384_{threads}_AUTONOMIC"):
            continue

        f = os.path.join(dir_name, filename)
        if not os.path.isfile(f):
            continue

        gvts += load_rs_stats_file(f, True)
        n += 1

    gvts /= n
    return gvts


def get_transition_data(dir_name, threads):
    data = np.zeros((lps_dim, lps_dim), dtype=float)

    n = 0
    for filename in os.listdir(dir_name):
        if not filename.endswith("_phases.txt") or not filename.startswith(f"tbc_16384_{threads}_AUTONOMIC"):
            continue

        f = os.path.join(dir_name, filename)
        if not os.path.isfile(f):
            continue

        with open(f, "r") as f:
            for i, l in enumerate(f):
                data[i // lps_dim][i % lps_dim] += int(l)
        n += 1

    for i in range(lps_dim):
        for j in range(lps_dim):
            data[i][j] /= n

    return data


def get_latencies_data(latency_file, threads):
    data = []
    with open(latency_file, "r") as f:
        for l in f.readlines()[1:threads + 1]:
            latencies = [int(v) for v in l.split(" ") if v][1:threads + 1]
            data.append(latencies)

    return np.array(data)


def plot_heatmap(dir_name, threads=1, latencies=None):
    plt.rcParams['font.family'] = ['monospace']
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots()

    ax.xaxis.set_ticks([0, lps_dim])
    ax.yaxis.set_ticks([0, lps_dim])
    ax.set_xlabel("x", labelpad=-10)
    ax.set_ylabel("y", rotation=0, labelpad=-15)

    gvts = get_gvts_count(dir_name, threads)
    data = get_transition_data(dir_name, threads)
    data = data - gvts
    data = data * -1.0

    im = ax.pcolormesh(data, cmap='Greens', edgecolors=(0.3, 0.3, 0.3), linewidth=0,
                       norm=mpl.colors.PowerNorm(1.5, vmin=0, vmax=gvts), rasterized=True)
    plt.gca().set_aspect('equal')

    lat_colors = ['maroon' for _ in range(threads - 1)]
    if latencies:
        lat_data = get_latencies_data(latencies, threads)
        adjacent_lat_data = [lat_data[i][i + 1] for i in range(threads - 1)]
        norm = mpl.colors.Normalize(vmin=min(adjacent_lat_data), vmax=max(adjacent_lat_data))
        cmap = mpl.cm.get_cmap('Reds')
        lat_colors = [cmap(norm(v)) for v in adjacent_lat_data]

    proc_load_data = get_precise_thread_load(dir_name, threads)
    proc_data_max = round(max(proc_load_data) + 1, -6) + 1000000
    norm = mpl.colors.Normalize(vmin=0, vmax=proc_data_max)
    cmap = mpl.cm.get_cmap('Blues')
    load_colors = [cmap(norm(v)) for v in proc_load_data]
    cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap))
    cbar.set_ticks([0, proc_data_max])
    cbar.set_label('Messages rollbacked', rotation=270, labelpad=2)

    cbar = fig.colorbar(im)
    cbar.set_ticks([0, gvts])
    cbar.set_ticklabels(["0%", "100%"])
    cbar.set_label('% of time in precise mode', rotation=270, labelpad=-15)

    ax.add_line(plt.Line2D((lps_dim, lps_dim), (0, lps_dim), linewidth=0.3, color="black", solid_capstyle='butt'))

    for i in reversed(range(lps_dim)):
        for j in range(lps_dim):
            tid = lpid_to_tid(lps_dim * lps_dim, i * lps_dim + j, threads)
            tid_up = lpid_to_tid(lps_dim * lps_dim, (i + 1) * lps_dim + j, threads)
            tid_left = lpid_to_tid(lps_dim * lps_dim, i * lps_dim + j + 1, threads)
            if tid != tid_up and i + 1 != lps_dim:
                ax.add_line(
                    plt.Line2D((j, j + 1), (i + 1, i + 1), linewidth=0.3, color=lat_colors[tid], solid_capstyle='butt'))

            if tid != tid_left and j + 1 != lps_dim:
                ax.add_line(
                    plt.Line2D((j + 1, j + 1), (i, i + 1), linewidth=0.3, color=lat_colors[tid], solid_capstyle='butt'))

    last_tid = 0
    first_i = 0
    for i in range(lps_dim):
        tid = lpid_to_tid(lps_dim * lps_dim, i * lps_dim + lps_dim - 1, threads)
        if last_tid != tid:
            ax.add_patch(mpl.patches.Rectangle((lps_dim, first_i), square_width, i - first_i,
                                               color=load_colors[last_tid], linewidth=0, rasterized=True))
            last_tid = tid
            first_i = i

    ax.add_patch(mpl.patches.Rectangle((lps_dim, first_i), square_width, lps_dim - first_i,
                                       color=load_colors[last_tid], linewidth=0, rasterized=True))

    ax.set_xlim([0, lps_dim + square_width])

    plt.savefig(f"autonomic_heatmap_{threads}.eps", dpi=300, bbox_inches='tight')
