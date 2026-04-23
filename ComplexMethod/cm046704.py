def _create_loss_plot(
        self, progress: TrainingProgress, theme: str = "light"
    ) -> plt.Figure:
        """Create training loss plot with theme-aware styling."""
        plt.close("all")

        LIGHT_STYLE = {
            "facecolor": "#ffffff",
            "grid_color": "#d1d5db",
            "line": "#16b88a",
            "text": "#1f2937",
            "empty_text": "#6b7280",
        }
        DARK_STYLE = {
            "facecolor": "#292929",
            "grid_color": "#404040",
            "line": "#4ade80",
            "text": "#e5e7eb",
            "empty_text": "#9ca3af",
        }

        style = LIGHT_STYLE if theme == "light" else DARK_STYLE

        fig, ax = plt.subplots(figsize = (PLOT_WIDTH, PLOT_HEIGHT))
        fig.patch.set_facecolor(style["facecolor"])
        ax.set_facecolor(style["facecolor"])

        if self.loss_history:
            steps = self.step_history
            losses = self.loss_history
            scatter_color = "#60a5fa"
            ax.scatter(
                steps,
                losses,
                s = 16,
                alpha = 0.6,
                color = scatter_color,
                linewidths = 0,
                label = "Training Loss (raw)",
            )

            MA_WINDOW = 20
            window = min(MA_WINDOW, len(losses))

            if window >= 2:
                cumsum = [0.0]
                for v in losses:
                    cumsum.append(cumsum[-1] + float(v))

                ma = []
                for i in range(len(losses)):
                    start = max(0, i - window + 1)
                    denom = i - start + 1
                    ma.append((cumsum[i + 1] - cumsum[start]) / denom)

                ax.plot(
                    steps,
                    ma,
                    color = style["line"],
                    linewidth = 2.5,
                    alpha = 0.95,
                    label = f"Moving Avg ({ma[-1]:.4f})",
                )

                leg = ax.legend(frameon = False, fontsize = 9)
                for t in leg.get_texts():
                    t.set_color(style["text"])

            ax.set_xlabel("Steps", fontsize = 10, color = style["text"])
            ax.set_ylabel("Loss", fontsize = 10, color = style["text"])

            if progress.error:
                title = f"Error: {progress.error}"
            elif progress.is_completed:
                loss_str = f"{progress.loss:.4f}" if progress.loss is not None else "--"
                title = f"Training completed! Final loss: {loss_str}"
            elif progress.status_message:
                title = progress.status_message
            elif progress.step > 0:
                loss_str = f"{progress.loss:.4f}" if progress.loss is not None else "--"
                title = f"Epoch: {progress.epoch} | Step: {progress.step}/{progress.total_steps} | Loss: {loss_str}"
            else:
                title = "Training Loss"

            ax.set_title(
                title, fontsize = 11, fontweight = "bold", pad = 10, color = style["text"]
            )
            ax.grid(True, alpha = 0.4, linestyle = "--", color = style["grid_color"])
            ax.tick_params(colors = style["text"], which = "both")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["bottom"].set_color(style["text"])
            ax.spines["left"].set_color(style["text"])
        else:
            display_msg = (
                progress.status_message
                if progress.status_message
                else "Waiting for training data..."
            )
            ax.text(
                0.5,
                0.5,
                display_msg,
                ha = "center",
                va = "center",
                fontsize = 16,
                color = style["empty_text"],
                transform = ax.transAxes,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)

        fig.tight_layout()
        return fig