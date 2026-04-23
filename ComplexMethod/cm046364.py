def plot(self, normalize: bool = True, save_dir: str = "", on_plot=None):
        """Plot the confusion matrix using matplotlib and save it to a file.

        Args:
            normalize (bool, optional): Whether to normalize the confusion matrix.
            save_dir (str, optional): Directory where the plot will be saved.
            on_plot (callable, optional): An optional callback to pass plots path and data when they are rendered.
        """
        import matplotlib.pyplot as plt  # scope for faster 'import ultralytics'

        array = self.matrix / ((self.matrix.sum(0).reshape(1, -1) + 1e-9) if normalize else 1)  # normalize columns
        array[array < 0.005] = np.nan  # don't annotate (would appear as 0.00)

        fig, ax = plt.subplots(1, 1, figsize=(12, 9))
        names, n = list(self.names.values()), self.nc
        if self.nc >= 100:  # downsample for large class count
            k = max(2, self.nc // 60)  # step size for downsampling, always > 1
            keep_idx = slice(None, None, k)  # create slice instead of array
            names = names[keep_idx]  # slice class names
            array = array[keep_idx, :][:, keep_idx]  # slice matrix rows and cols
            n = (self.nc + k - 1) // k  # number of retained classes
        nc = n if self.task == "classify" else n + 1  # adjust for background if needed
        ticklabels = "auto"
        if 0 < nc < 99:
            ticklabels = names if self.task == "classify" else [*names, "background"]
        xy_ticks = np.arange(len(ticklabels)) if ticklabels != "auto" else np.arange(nc)
        tick_fontsize = max(6, 15 - 0.1 * nc)  # Minimum size is 6
        label_fontsize = max(6, 12 - 0.1 * nc)
        title_fontsize = max(6, 12 - 0.1 * nc)
        btm = max(0.1, 0.25 - 0.001 * nc)  # Minimum value is 0.1
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # suppress empty matrix RuntimeWarning: All-NaN slice encountered
            im = ax.imshow(array, cmap="Blues", vmin=0.0, interpolation="none")
            ax.xaxis.set_label_position("bottom")
            if nc < 30:  # Add score for each cell of confusion matrix
                color_threshold = 0.45 * (1 if normalize else np.nanmax(array))  # text color threshold
                for i, row in enumerate(array[:nc]):
                    for j, val in enumerate(row[:nc]):
                        val = array[i, j]
                        if np.isnan(val):
                            continue
                        ax.text(
                            j,
                            i,
                            f"{val:.2f}" if normalize else f"{int(val)}",
                            ha="center",
                            va="center",
                            fontsize=10,
                            color="white" if val > color_threshold else "black",
                        )
            cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.05)
        title = "Confusion Matrix" + " Normalized" * normalize
        ax.set_xlabel("True", fontsize=label_fontsize, labelpad=10)
        ax.set_ylabel("Predicted", fontsize=label_fontsize, labelpad=10)
        ax.set_title(title, fontsize=title_fontsize, pad=20)
        ax.set_xticks(xy_ticks)
        ax.set_yticks(xy_ticks)
        ax.tick_params(axis="x", bottom=True, top=False, labelbottom=True, labeltop=False)
        ax.tick_params(axis="y", left=True, right=False, labelleft=True, labelright=False)
        if ticklabels != "auto":
            ax.set_xticklabels(ticklabels, fontsize=tick_fontsize, rotation=90, ha="center")
            ax.set_yticklabels(ticklabels, fontsize=tick_fontsize)
        for s in {"left", "right", "bottom", "top", "outline"}:
            if s != "outline":
                ax.spines[s].set_visible(False)  # Confusion matrix plot don't have outline
            cbar.ax.spines[s].set_visible(False)
        fig.subplots_adjust(left=0, right=0.84, top=0.94, bottom=btm)  # Adjust layout to ensure equal margins
        plot_fname = Path(save_dir) / f"{title.lower().replace(' ', '_')}.png"
        fig.savefig(plot_fname, dpi=250)
        plt.close(fig)
        if on_plot:
            on_plot(plot_fname, {"type": "confusion_matrix", "matrix": self.matrix.tolist()})