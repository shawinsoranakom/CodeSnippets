def plot_results(file: str = "path/to/results.csv", dir: str = "", on_plot: Callable | None = None):
    """Plot training results from a results CSV file. The function supports various types of data including
    segmentation, pose estimation, and classification. Plots are saved as 'results.png' in the directory where the
    CSV is located.

    Args:
        file (str, optional): Path to the CSV file containing the training results.
        dir (str, optional): Directory where the CSV file is located if 'file' is not provided.
        on_plot (Callable, optional): Callback function to be executed after plotting. Takes filename as an argument.

    Examples:
        >>> from ultralytics.utils.plotting import plot_results
        >>> plot_results("path/to/results.csv")
    """
    import matplotlib.pyplot as plt  # scope for faster 'import ultralytics'
    import polars as pl
    from scipy.ndimage import gaussian_filter1d

    save_dir = Path(file).parent if file else Path(dir)
    files = list(save_dir.glob("results*.csv"))
    assert len(files), f"No results.csv files found in {save_dir.resolve()}, nothing to plot."

    loss_keys, metric_keys = [], []
    for i, f in enumerate(files):
        try:
            data = pl.read_csv(f, infer_schema_length=None)
            if i == 0:
                for c in data.columns:
                    if "loss" in c:
                        loss_keys.append(c)
                    elif "metric" in c:
                        metric_keys.append(c)
                loss_mid, metric_mid = len(loss_keys) // 2, len(metric_keys) // 2
                columns = (
                    loss_keys[:loss_mid] + metric_keys[:metric_mid] + loss_keys[loss_mid:] + metric_keys[metric_mid:]
                )
                fig, ax = plt.subplots(2, len(columns) // 2, figsize=(len(columns) + 2, 6), tight_layout=True)
                ax = ax.ravel()
            x = data.select(data.columns[0]).to_numpy().flatten()
            for i, j in enumerate(columns):
                y = data.select(j).to_numpy().flatten().astype("float")
                ax[i].plot(x, y, marker=".", label=f.stem, linewidth=2, markersize=8)  # actual results
                ax[i].plot(x, gaussian_filter1d(y, sigma=3), ":", label="smooth", linewidth=2)  # smoothing line
                ax[i].set_title(j, fontsize=12)
        except Exception as e:
            LOGGER.error(f"Plotting error for {f}: {e}")
    ax[1].legend()
    fname = save_dir / "results.png"
    fig.savefig(fname, dpi=200)
    plt.close()
    if on_plot:
        on_plot(fname)