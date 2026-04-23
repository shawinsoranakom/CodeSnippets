def draw_thread_status(self, line, width):
        """Draw thread status statistics and GC information."""
        # Get status counts for current view mode
        thread_data = self.collector._get_current_thread_data()
        status_counts = thread_data.as_status_dict() if thread_data else self.collector.thread_status_counts

        # Calculate percentages
        total_threads = max(1, status_counts["total"])
        pct_on_gil = (status_counts["has_gil"] / total_threads) * 100
        pct_off_gil = 100.0 - pct_on_gil
        pct_gil_requested = (status_counts["gil_requested"] / total_threads) * 100
        pct_exception = (status_counts.get("has_exception", 0) / total_threads) * 100

        # Get GC percentage based on view mode
        if thread_data:
            total_samples = max(1, thread_data.sample_count)
            pct_gc = (thread_data.gc_frame_samples / total_samples) * 100
        else:
            # Use total_samples for GC percentage since gc_frame_samples is tracked
            # across ALL samples (via thread status), not just successful ones
            total_samples = max(1, self.collector.total_samples)
            pct_gc = (self.collector.gc_frame_samples / total_samples) * 100

        col = 0
        self.add_str(line, col, "Threads:   ", curses.A_BOLD)
        col += 11

        # Show GIL stats only if mode is not GIL (GIL mode filters to only GIL holders)
        if self.collector.mode != PROFILING_MODE_GIL:
            col = self._add_percentage_stat(
                line, col, pct_on_gil, "on gil", self.colors["green"]
            )
            col = self._add_percentage_stat(
                line,
                col,
                pct_off_gil,
                "off gil",
                self.colors["red"],
                add_separator=True,
            )

        # Show "waiting for gil" only if mode is not GIL
        if self.collector.mode != PROFILING_MODE_GIL and col < width - 30:
            col = self._add_percentage_stat(
                line,
                col,
                pct_gil_requested,
                "waiting for gil",
                self.colors["yellow"],
                add_separator=True,
            )

        # Show exception stats
        if col < width - 15:
            col = self._add_percentage_stat(
                line,
                col,
                pct_exception,
                "exc",
                self.colors["red"],
                add_separator=(col > 11),
            )

        # Always show GC stats
        if col < width - 15:
            col = self._add_percentage_stat(
                line,
                col,
                pct_gc,
                "GC",
                self.colors["magenta"],
                add_separator=(col > 11),
            )

        return line + 1