def _plot_fig(
    fig_dir: Path,
    fig_group_data: tuple[tuple[tuple[str, str], ...], list[dict[str, object]]],
    label_by: list[str],
    *,
    dry_run: bool,
):
    fig_group, fig_data = fig_group_data
    fig_path = _get_fig_path(fig_dir, fig_group)

    print("[BEGIN FIGURE]")
    print(f"Group: {dict(fig_group)}")
    print(f"Output file: {fig_path}")

    if dry_run:
        print("[END FIGURE]")
        return

    # Lazy-import matplotlib/pandas/seaborn
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        plt = PlaceholderModule("matplotlib").placeholder_attr("pyplot")
    try:
        import pandas as pd
    except ImportError:
        pd = PlaceholderModule("pandas")
    try:
        import seaborn as sns
    except ImportError:
        sns = PlaceholderModule("seaborn")

    df = pd.DataFrame.from_records(fig_data)
    df = df.dropna(subset=["tokens_per_user", "tokens_per_gpu"])

    if df.empty:
        print("No data points available after filtering; skipping.")
        print("[END FIGURE]")
        return

    frontier = _pareto_frontier(df, "tokens_per_user", "tokens_per_gpu")
    frontier = frontier.sort_values("tokens_per_user")

    fig, ax = plt.subplots()
    sns.scatterplot(
        data=df,
        x="tokens_per_user",
        y="tokens_per_gpu",
        color="0.5",
        alpha=0.6,
        ax=ax,
        label="All runs",
    )
    sns.lineplot(
        data=frontier,
        x="tokens_per_user",
        y="tokens_per_gpu",
        marker="o",
        ax=ax,
        label="Pareto frontier",
    )

    if label_by:
        for _, row in frontier.iterrows():
            label_parts = []
            for key in label_by:
                if key in row:
                    label_parts.append(f"{key}={row[key]}")
            if label_parts:
                ax.text(
                    row["tokens_per_user"],
                    row["tokens_per_gpu"],
                    "\n".join(label_parts),
                    fontsize=8,
                )

    ax.set_xlabel("Tokens/s/user")
    ax.set_ylabel("Tokens/s/GPU")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    fig.tight_layout()
    fig.savefig(fig_path)
    plt.close(fig)

    print(
        f"Plotted {len(df)} points; Pareto frontier size: {len(frontier)}.",
    )
    print("[END FIGURE]")