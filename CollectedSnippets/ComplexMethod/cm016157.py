def visualize_comparison(
    profiling_results: dict[str, list[Performance]],
    title: str | None = None,
    output_path: str | None = None,
) -> None:
    """
    Create a single memory_bandwidth comparison plot from profiling results.

    Args:
        profiling_results: Dict mapping backend names to lists of Performance objects
        output_path: Path to save the plot (optional)
    """
    # Get backend colors
    backend_colors = get_backend_colors()

    # Extract settings from eager backend which runs all settings
    all_settings = []
    for perf in profiling_results["eager"]:
        all_settings.append(perf.setting)

    # Create single plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    for backend in profiling_results:
        backend_perfs = profiling_results[backend]
        perf_dict = {perf.setting: perf for perf in backend_perfs}

        x_vals = []
        y_vals = []
        for i, setting in enumerate(all_settings):
            if setting in perf_dict:
                x_vals.append(i)
                y_vals.append(perf_dict[setting].memory_bandwidth)

        if x_vals:  # Only plot if we have data
            color = backend_colors.get(backend, backend_colors["default"])
            ax.plot(
                x_vals,
                y_vals,
                "o-",
                label=backend,
                color=color,
                linewidth=2,
                markersize=8,
                alpha=0.8,
            )

    # Configure the plot
    ax.set_title(title or "Memory Bandwidth Comparison", fontsize=16)
    ax.set_xlabel("Shape", fontsize=12)
    ax.set_ylabel("memory bandwidth (GB/s)", fontsize=12)
    ax.set_xticks(range(len(all_settings)))
    ax.set_xticklabels(
        [
            s.replace("shape: ", "").replace("[", "").replace("]", "")
            for s in all_settings
        ],
        rotation=45,
        ha="right",
    )
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save the plot if output path is provided
    if output_path:
        # Save as PNG
        os.makedirs("pics", exist_ok=True)
        full_path = os.path.join("pics", output_path + ".png")
        plt.savefig(full_path, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"Chart saved to {full_path}")

    plt.close()