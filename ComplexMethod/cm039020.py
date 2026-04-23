def plot_trace_df(
    traces_df: "pd.DataFrame",
    plot_metric: str,
    plot_title: str,
    output: Path | None = None,
):
    def get_phase_description(traces_df: "pd.DataFrame", phase: str) -> str:
        phase_df = traces_df.query(f'phase == "{phase}"')
        descs = phase_df["phase_desc"].to_list()
        assert all([desc == descs[0] for desc in descs])
        return descs[0]

    phases = traces_df["phase"].unique()
    phase_descs = [get_phase_description(traces_df, p) for p in phases]
    traces_df = traces_df.pivot_table(
        index="phase", columns="name", values=plot_metric, aggfunc="sum"
    )

    traces_df = group_trace_by_operations(traces_df)

    # Make the figure
    fig_size_x = max(5, len(phases))
    fig, ax = plt.subplots(1, figsize=(fig_size_x, 8), sharex=True)

    # Draw the stacked bars
    ops = list(traces_df)
    bottom = [0] * len(phases)
    for op in ops:
        values = [traces_df[op][phase] for phase in phases]
        values = list(map(lambda x: 0.0 if math.isnan(x) else x, values))
        ax.bar(phase_descs, values, label=op, bottom=bottom)
        bottom = [bottom[j] + values[j] for j in range(len(phases))]

    # Write the values as text on the bars
    for bar in ax.patches:
        if bar.get_height() != 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() / 2 + bar.get_y(),
                f"{round(bar.get_height(), 2)}",
                ha="center",
                color="w",
                weight="bold",
                size=5,
            )

    # Setup legend
    handles, labels = plt.gca().get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="center left", bbox_to_anchor=(1, 1))
    shorten_plot_legend_strings(legend, 50)

    # Setup labels and title
    plt.setp(ax.get_xticklabels(), rotation=90)
    ax.set_ylabel(plot_metric)
    plt.suptitle(plot_title)

    plt.savefig(output, bbox_inches="tight")
    print("Created: ", output)