def create_total_tokens_plot(all_results):
    num_strategies = len(all_results)
    num_configs = len(configs)

    fig, axs = plt.subplots(
        num_strategies, num_configs * 2, figsize=(32, 8 * num_strategies)
    )

    # Add main title to the entire figure
    fig.suptitle(
        "Performance Analysis: Speedup vs Bandwidth Utilization (SiLU V2, and Triton)",
        fontsize=18,
        fontweight="bold",
        y=0.98,
    )

    # Handle single strategy case
    if num_strategies == 1:
        axs = axs.reshape(1, -1)

    # Handle single config case
    if num_configs == 1:
        axs = axs.reshape(-1, 2)

    for strategy_idx, result in enumerate(all_results):
        (
            strategy_name,
            all_ratios,
            all_silu_v2_results,
            all_triton_results,
            config_labels,
            config_x_axis,
        ) = result

        for config_idx in range(num_configs):
            # Speedup plot (left column)
            ax_speedup = axs[strategy_idx, config_idx * 2]
            # Bandwidth plot (right column)
            ax_bandwidth = axs[strategy_idx, config_idx * 2 + 1]

            E, T, H = configs[config_idx]
            ratios = all_ratios[config_idx]
            total_tokens_values = config_x_axis[config_idx]

            # Extract speedup ratios
            triton_v2_ratios = [ratio for ratio in ratios]

            # Extract bandwidth percentages for all implementations
            v2_bandwidth_percentages = [
                result[3] for result in all_silu_v2_results[config_idx]
            ]
            triton_bandwidth_percentages = [
                result[3] for result in all_triton_results[config_idx]
            ]

            # Plot speedup ratios vs total tokens (left plot)
            ax_speedup.plot(
                total_tokens_values,
                triton_v2_ratios,
                "go-",
                linewidth=3,
                markersize=8,
                label="Triton/V2 Speedup",
            )
            ax_speedup.set_title(
                f"{strategy_name}\nSpeedup vs Baseline (Triton)\nE={E}, T={T}, H={H}",
                fontsize=12,
                fontweight="bold",
            )
            ax_speedup.set_xlabel("Total Tokens", fontweight="bold", fontsize=11)
            ax_speedup.set_ylabel("Speedup Ratio", fontweight="bold", fontsize=11)
            ax_speedup.legend(prop={"weight": "bold"})
            ax_speedup.grid(True, alpha=0.3)

            # Plot bandwidth utilization (right plot)
            ax_bandwidth.plot(
                total_tokens_values,
                v2_bandwidth_percentages,
                "o-",
                linewidth=3,
                markersize=8,
                label="SiLU V2",
                color="blue",
            )
            ax_bandwidth.plot(
                total_tokens_values,
                triton_bandwidth_percentages,
                "o-",
                linewidth=3,
                markersize=8,
                label="Triton",
                color="green",
            )
            ax_bandwidth.set_title(
                f"{strategy_name}\nBandwidth Utilization (Hopper)\nE={E}, T={T}, H={H}",
                fontsize=12,
                fontweight="bold",
            )
            ax_bandwidth.set_xlabel("Total Tokens", fontweight="bold", fontsize=11)
            ax_bandwidth.set_ylabel(
                "% of Peak Bandwidth", fontweight="bold", fontsize=11
            )
            ax_bandwidth.legend(prop={"weight": "bold"})
            ax_bandwidth.grid(True, alpha=0.3)

            # Format x-axis labels for both plots
            for ax in [ax_speedup, ax_bandwidth]:
                ax.set_xticks(total_tokens_values)
                ax.set_xticklabels(
                    [
                        f"{tt // 1000}K" if tt >= 1000 else str(tt)
                        for tt in total_tokens_values
                    ],
                    fontweight="bold",
                )
                # Make tick labels bold
                for label in ax.get_xticklabels() + ax.get_yticklabels():
                    label.set_fontweight("bold")

            # Add value labels on Triton/V2 speedup points
            for x, y in zip(total_tokens_values, triton_v2_ratios):
                ax_speedup.annotate(
                    f"{y:.2f}x",
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, -15),
                    ha="center",
                    fontsize=9,
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="green", alpha=0.3),
                )

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)  # Make room for main title
    filename = "silu_benchmark_total_tokens_3way.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()

    return filename