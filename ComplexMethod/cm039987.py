def plot(outname=None):
    import pandas as pd

    with open("bench_saga.json", "r") as f:
        f = json.load(f)
    res = pd.DataFrame(f)
    res.set_index(["single_target"], inplace=True)

    grouped = res.groupby(level=["single_target"])

    colors = {"saga": "C0", "liblinear": "C1", "lightning": "C2"}
    linestyles = {"float32": "--", "float64": "-"}
    alpha = {"float64": 0.5, "float32": 1}

    for idx, group in grouped:
        single_target = idx
        fig, axes = plt.subplots(figsize=(12, 4), ncols=4)
        ax = axes[0]

        for scores, times, solver, dtype in zip(
            group["train_scores"], group["times"], group["solver"], group["dtype"]
        ):
            ax.plot(
                times,
                scores,
                label="%s - %s" % (solver, dtype),
                color=colors[solver],
                alpha=alpha[dtype],
                marker=".",
                linestyle=linestyles[dtype],
            )
            ax.axvline(
                times[-1],
                color=colors[solver],
                alpha=alpha[dtype],
                linestyle=linestyles[dtype],
            )
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Training objective (relative to min)")
        ax.set_yscale("log")

        ax = axes[1]

        for scores, times, solver, dtype in zip(
            group["test_scores"], group["times"], group["solver"], group["dtype"]
        ):
            ax.plot(
                times,
                scores,
                label=solver,
                color=colors[solver],
                linestyle=linestyles[dtype],
                marker=".",
                alpha=alpha[dtype],
            )
            ax.axvline(
                times[-1],
                color=colors[solver],
                alpha=alpha[dtype],
                linestyle=linestyles[dtype],
            )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Test objective (relative to min)")
        ax.set_yscale("log")

        ax = axes[2]
        for accuracy, times, solver, dtype in zip(
            group["accuracies"], group["times"], group["solver"], group["dtype"]
        ):
            ax.plot(
                times,
                accuracy,
                label="%s - %s" % (solver, dtype),
                alpha=alpha[dtype],
                marker=".",
                color=colors[solver],
                linestyle=linestyles[dtype],
            )
            ax.axvline(
                times[-1],
                color=colors[solver],
                alpha=alpha[dtype],
                linestyle=linestyles[dtype],
            )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Test accuracy")
        ax.legend()
        name = "single_target" if single_target else "multi_target"
        name += "_%s" % penalty
        plt.suptitle(name)
        if outname is None:
            outname = name + ".png"
        fig.tight_layout()
        fig.subplots_adjust(top=0.9)

        ax = axes[3]
        for scores, times, solver, dtype in zip(
            group["train_scores"], group["times"], group["solver"], group["dtype"]
        ):
            ax.plot(
                np.arange(len(scores)),
                scores,
                label="%s - %s" % (solver, dtype),
                marker=".",
                alpha=alpha[dtype],
                color=colors[solver],
                linestyle=linestyles[dtype],
            )

        ax.set_yscale("log")
        ax.set_xlabel("# iterations")
        ax.set_ylabel("Objective function")
        ax.legend()

        plt.savefig(outname)