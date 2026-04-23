def profile_idetection(start=0, stop=0, labels=(), save_dir=""):
    """Plots per-image iDetection logs, comparing metrics like storage and performance over time.

    Example: from utils.plots import *; profile_idetection()
    """
    ax = plt.subplots(2, 4, figsize=(12, 6), tight_layout=True)[1].ravel()
    s = ["Images", "Free Storage (GB)", "RAM Usage (GB)", "Battery", "dt_raw (ms)", "dt_smooth (ms)", "real-world FPS"]
    files = list(Path(save_dir).glob("frames*.txt"))
    for fi, f in enumerate(files):
        try:
            results = np.loadtxt(f, ndmin=2).T[:, 90:-30]  # clip first and last rows
            n = results.shape[1]  # number of rows
            x = np.arange(start, min(stop, n) if stop else n)
            results = results[:, x]
            t = results[0] - results[0].min()  # set t0=0s
            results[0] = x
            for i, a in enumerate(ax):
                if i < len(results):
                    label = labels[fi] if len(labels) else f.stem.replace("frames_", "")
                    a.plot(t, results[i], marker=".", label=label, linewidth=1, markersize=5)
                    a.set_title(s[i])
                    a.set_xlabel("time (s)")
                    # if fi == len(files) - 1:
                    #     a.set_ylim(bottom=0)
                    for side in ["top", "right"]:
                        a.spines[side].set_visible(False)
                else:
                    a.remove()
        except Exception as e:
            print(f"Warning: Plotting error for {f}; {e}")
    ax[1].legend()
    plt.savefig(Path(save_dir) / "idetection_profile.png", dpi=200)