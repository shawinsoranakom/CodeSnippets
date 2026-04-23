def process(self, im0: np.ndarray, frame_number: int) -> SolutionResults:
        """Process image data and run object tracking to update analytics charts.

        Args:
            im0 (np.ndarray): Input image for processing.
            frame_number (int): Video frame number for plotting the data.

        Returns:
            (SolutionResults): Contains processed image `plot_im`, 'total_tracks' (int, total number of tracked objects)
                and 'classwise_count' (dict, per-class object count).

        Raises:
            ValueError: If an unsupported chart type is specified.

        Examples:
            >>> analytics = Analytics(analytics_type="line")
            >>> frame = np.zeros((480, 640, 3), dtype=np.uint8)
            >>> results = analytics.process(frame, frame_number=1)
        """
        self.extract_tracks(im0)  # Extract tracks
        if self.type == "line":
            for _ in self.boxes:
                self.total_counts += 1
            update_required = frame_number % self.update_every == 0 or self.last_plot_im is None
            if update_required:
                self.last_plot_im = self.update_graph(frame_number=frame_number)
            plot_im = self.last_plot_im
            self.total_counts = 0
        elif self.type in {"pie", "bar", "area"}:
            from collections import Counter

            self.clswise_count = Counter(self.names[int(cls)] for cls in self.clss)
            update_required = frame_number % self.update_every == 0 or self.last_plot_im is None
            if update_required:
                self.last_plot_im = self.update_graph(
                    frame_number=frame_number, count_dict=self.clswise_count, plot=self.type
                )
            plot_im = self.last_plot_im
        else:
            raise ValueError(f"Unsupported analytics_type='{self.type}'. Supported types: line, bar, pie, area.")

        # Return results for downstream use.
        return SolutionResults(plot_im=plot_im, total_tracks=len(self.track_ids), classwise_count=self.clswise_count)