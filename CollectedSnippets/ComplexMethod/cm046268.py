def update_graph(
        self, frame_number: int, count_dict: dict[str, int] | None = None, plot: str = "line"
    ) -> np.ndarray:
        """Update the graph with new data for single or multiple classes.

        Args:
            frame_number (int): The current frame number.
            count_dict (dict[str, int], optional): Dictionary with class names as keys and counts as values for multiple
                classes. If None, updates a single line graph.
            plot (str): Type of the plot. Options are 'line', 'bar', 'pie', or 'area'.

        Returns:
            (np.ndarray): Updated image containing the graph.

        Examples:
            >>> analytics = Analytics(analytics_type="bar")
            >>> frame_num = 10
            >>> results_dict = {"person": 5, "car": 3}
            >>> updated_image = analytics.update_graph(frame_num, results_dict, plot="bar")
        """
        if count_dict is None:
            # Single line update
            x_data = np.append(self.line.get_xdata(), float(frame_number))
            y_data = np.append(self.line.get_ydata(), float(self.total_counts))

            if len(x_data) > self.max_points:
                x_data, y_data = x_data[-self.max_points :], y_data[-self.max_points :]

            self.line.set_data(x_data, y_data)
            self.line.set_label("Counts")
            self.line.set_color("#7b0068")  # Pink color
            self.line.set_marker("*")
            self.line.set_markersize(self.line_width * 5)
        else:
            labels = list(count_dict.keys())
            counts = list(count_dict.values())
            if plot == "area":
                color_cycle = cycle(["#DD00BA", "#042AFF", "#FF4447", "#7D24FF", "#BD00FF"])
                # Multiple lines or area update
                x_data = self.ax.lines[0].get_xdata() if self.ax.lines else np.array([])
                y_data_dict = {key: np.array([]) for key in count_dict.keys()}
                if self.ax.lines:
                    for line, key in zip(self.ax.lines, count_dict.keys()):
                        y_data_dict[key] = line.get_ydata()

                x_data = np.append(x_data, float(frame_number))
                max_length = len(x_data)
                for key in count_dict.keys():
                    y_data_dict[key] = np.append(y_data_dict[key], float(count_dict[key]))
                    if len(y_data_dict[key]) < max_length:
                        y_data_dict[key] = np.pad(y_data_dict[key], (0, max_length - len(y_data_dict[key])))
                if len(x_data) > self.max_points:
                    x_data = x_data[1:]
                    for key in count_dict.keys():
                        y_data_dict[key] = y_data_dict[key][1:]

                self.ax.clear()
                for key, y_data in y_data_dict.items():
                    color = next(color_cycle)
                    self.ax.fill_between(x_data, y_data, color=color, alpha=0.55)
                    self.ax.plot(
                        x_data,
                        y_data,
                        color=color,
                        linewidth=self.line_width,
                        marker="o",
                        markersize=self.line_width * 5,
                        label=f"{key} Data Points",
                    )
            elif plot == "bar":
                self.ax.clear()  # clear bar data
                for label in labels:  # Map labels to colors
                    if label not in self.color_mapping:
                        self.color_mapping[label] = next(self.color_cycle)
                colors = [self.color_mapping[label] for label in labels]
                bars = self.ax.bar(labels, counts, color=colors)
                for bar, count in zip(bars, counts):
                    self.ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height(),
                        str(count),
                        ha="center",
                        va="bottom",
                        color=self.fg_color,
                    )
                # Create the legend using labels from the bars
                for bar, label in zip(bars, labels):
                    bar.set_label(label)  # Assign label to each bar
                self.ax.legend(loc="upper left", fontsize=13, facecolor=self.fg_color, edgecolor=self.fg_color)
            elif plot == "pie":
                total = sum(counts)
                percentages = [size / total * 100 for size in counts]
                self.ax.clear()

                start_angle = 90
                # Create pie chart and create legend labels with percentages
                wedges, _ = self.ax.pie(
                    counts, labels=labels, startangle=start_angle, textprops={"color": self.fg_color}, autopct=None
                )
                legend_labels = [f"{label} ({percentage:.1f}%)" for label, percentage in zip(labels, percentages)]

                # Assign the legend using the wedges and manually created labels
                self.ax.legend(wedges, legend_labels, title="Classes", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
                self.fig.subplots_adjust(left=0.1, right=0.75)  # Adjust layout to fit the legend

        # Common plot settings
        self.ax.set_facecolor("#f0f0f0")  # Set to light gray or any other color you like
        self.ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)  # Display grid for more data insights
        self.ax.set_title(self.title, color=self.fg_color, fontsize=self.fontsize)
        self.ax.set_xlabel(self.x_label, color=self.fg_color, fontsize=self.fontsize - 3)
        self.ax.set_ylabel(self.y_label, color=self.fg_color, fontsize=self.fontsize - 3)

        # Add and format legend
        legend = self.ax.legend(loc="upper left", fontsize=13, facecolor=self.bg_color, edgecolor=self.bg_color)
        for text in legend.get_texts():
            text.set_color(self.fg_color)

        # Redraw graph, update view, capture, and display the updated plot
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()
        im0 = np.array(self.canvas.renderer.buffer_rgba())
        im0 = cv2.cvtColor(im0[:, :, :3], cv2.COLOR_RGBA2BGR)
        self.display_output(im0)

        return im0