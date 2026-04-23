def create_combined_plot(all_results):
    num_strategies = len(all_results)
    fig, axes = plt.subplots(num_strategies, 1, figsize=(22, 7 * num_strategies))

    if num_strategies == 1:
        axes = [axes]

    for idx, (
        strategy_name,
        all_ratios,
        all_silu_v2_results,
        all_triton_results,
        config_labels,
        config_x_axis,
    ) in enumerate(all_results):
        ax = axes[idx]

        # Flatten the nested results to get bandwidth percentages for plotting
        silu_v2_bandwidths = []
        triton_bandwidths = []
        flat_ratios = []

        for config_results in all_silu_v2_results:
            for result in config_results:
                silu_v2_bandwidths.append(result[3])  # bandwidth percentage

        for config_results in all_triton_results:
            for result in config_results:
                triton_bandwidths.append(result[3])  # bandwidth percentage

        for config_ratios in all_ratios:
            for ratio in config_ratios:
                flat_ratios.append(ratio)

        # Configure x-axis positions
        x = np.arange(len(config_labels))
        width = 0.25

        # Bandwidth utilization plot (higher is better)
        ax.bar(
            x,
            silu_v2_bandwidths,
            width,
            label="SiLU V2 (CUDA)",
            alpha=0.8,
            color="blue",
        )
        ax.bar(
            x + width,
            triton_bandwidths,
            width,
            label="Triton Kernel",
            alpha=0.8,
            color="green",
        )

        # Add speedup labels over each bar trio
        for i in range(len(x)):
            triton_v2_speedup = flat_ratios[i]  # triton/v2
            max_height = max(silu_v2_bandwidths[i], triton_bandwidths[i])

            # Triton/V2 speedup
            ax.text(
                x[i] + width / 2,
                max_height + max_height * 0.02,
                f"{triton_v2_speedup:.2f}x",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=8,
            )

        ax.set_xlabel("Configuration")
        ax.set_ylabel("% Utilization")
        ax.set_title(
            f"Memory Bandwidth Utilization (%) - {strategy_name}\n(Higher is Better)"
        )
        ax.set_xticks(x)
        ax.set_xticklabels(config_labels, rotation=45, ha="right")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    filename = "silu_benchmark_combined_3way.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()

    return filename