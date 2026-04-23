def plot_tune_results(results_file: str = "tune_results.ndjson", exclude_zero_fitness_points: bool = True):
    """Plot the evolution results stored in a tuning NDJSON file.

    Args:
        results_file (str, optional): Path to the NDJSON file containing the tuning results.
        exclude_zero_fitness_points (bool, optional): Don't include points with zero fitness in tuning plots.

    Examples:
        >>> plot_tune_results("path/to/tune_results.ndjson")
    """
    import json

    import matplotlib.pyplot as plt  # scope for faster 'import ultralytics'
    from scipy.ndimage import gaussian_filter1d

    def _save_one_file(file):
        """Save one matplotlib plot to 'file'."""
        plt.savefig(file, dpi=200)
        plt.close()
        LOGGER.info(f"Saved {file}")

    results_file = Path(results_file)
    with open(results_file, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    if not records:
        return

    keys = list(records[0].get("hyperparameters", {}))
    x = np.array(
        [[r.get("fitness", 0.0)] + [r.get("hyperparameters", {}).get(k, np.nan) for k in keys] for r in records],
        dtype=float,
    )
    len(x)
    all_fitness = x[:, 0]  # fitness
    zero_mask = slice(None)
    if exclude_zero_fitness_points:
        zero_mask = all_fitness > 0  # exclude zero-fitness points
        x, all_fitness = x[zero_mask], all_fitness[zero_mask]
    if len(all_fitness) == 0:
        LOGGER.warning("No valid fitness values to plot (all iterations may have failed)")
        return
    fitness = all_fitness.copy()
    # Iterative sigma rejection on lower bound only
    for _ in range(3):  # max 3 iterations
        mean, std = fitness.mean(), fitness.std()
        lower_bound = mean - 3 * std
        mask = fitness >= lower_bound
        if mask.all():  # no more outliers
            break
        x, fitness = x[mask], fitness[mask]
    j = np.argmax(fitness)  # max fitness index
    n = math.ceil(len(keys) ** 0.5)  # columns and rows in plot
    plt.figure(figsize=(10, 10), tight_layout=True)
    for i, k in enumerate(keys):
        v = x[:, i + 1]
        mu = v[j]  # best single result
        plt.subplot(n, n, i + 1)
        plt_color_scatter(v, fitness, cmap="viridis", alpha=0.8, edgecolors="none")
        plt.plot(mu, fitness.max(), "k+", markersize=15)
        plt.title(f"{k} = {mu:.3g}", fontdict={"size": 9})  # limit to 40 characters
        plt.tick_params(axis="both", labelsize=8)  # Set axis label size to 8
        if i % n != 0:
            plt.yticks([])
    _save_one_file(results_file.with_name("tune_scatter_plots.png"))

    # Fitness vs iteration
    x = range(1, len(all_fitness) + 1)
    plt.figure(figsize=(10, 6), tight_layout=True)
    for dataset in sorted({k for r in records for k in r.get("datasets", {})}):
        y = np.array([r.get("datasets", {}).get(dataset, {}).get("fitness", np.nan) for r in records], dtype=float)
        if exclude_zero_fitness_points and not isinstance(zero_mask, slice):
            y = y[zero_mask]
        plt.plot(x, y, "o", markersize=5, alpha=0.8, label=dataset)
    plt.plot(x, gaussian_filter1d(all_fitness, sigma=3), ":", color="0.35", label="smoothed mean", linewidth=2)
    plt.title("Fitness vs Iteration")
    plt.xlabel("Iteration")
    plt.ylabel("Fitness")
    plt.grid(True)
    plt.legend()
    _save_one_file(results_file.with_name("tune_fitness.png"))