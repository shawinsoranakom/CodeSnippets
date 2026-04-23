def draw_sample_stats(self, line, width, elapsed):
        """Draw sample statistics with visual progress bar."""
        sample_rate = (
            self.collector.total_samples / elapsed if elapsed > 0 else 0
        )

        # Update max sample rate
        if sample_rate > self.collector.max_sample_rate:
            self.collector.max_sample_rate = sample_rate

        col = 0
        self.add_str(line, col, "Samples: ", curses.A_BOLD)
        col += 9
        self.add_str(
            line,
            col,
            f"{self.collector.total_samples:>8}",
            self.colors["cyan"],
        )
        col += 8
        self.add_str(
            line, col, f" total ({sample_rate:>7.1f}/s) ", curses.A_NORMAL
        )
        col += 23

        # Draw sample rate bar
        target_rate = (
            MICROSECONDS_PER_SECOND / self.collector.sample_interval_usec
        )

        # Show current/target ratio with percentage
        if sample_rate > 0 and target_rate > 0:
            percentage = min((sample_rate / target_rate) * 100, 100)
            current_formatted = self.format_rate_with_units(sample_rate)
            target_formatted = self.format_rate_with_units(target_rate)

            if percentage >= 99.5:  # Show 100% when very close
                rate_label = f" {current_formatted}/{target_formatted} (100%)"
            else:
                rate_label = f" {current_formatted}/{target_formatted} ({percentage:>4.1f}%)"
        else:
            target_formatted = self.format_rate_with_units(target_rate)
            rate_label = f" target: {target_formatted}"

        available_width = width - col - len(rate_label) - 3

        if available_width >= MIN_BAR_WIDTH:
            bar_width = min(MAX_SAMPLE_RATE_BAR_WIDTH, available_width)
            # Use target rate as the reference, with a minimum for scaling
            reference_rate = max(target_rate, MIN_SAMPLE_RATE_FOR_SCALING)
            normalized_rate = min(sample_rate / reference_rate, 1.0)
            bar_fill = int(normalized_rate * bar_width)

            bar = "["
            for i in range(bar_width):
                bar += "█" if i < bar_fill else "░"
            bar += "]"
            self.add_str(line, col, bar, self.colors["green"])
            col += len(bar)

            if col + len(rate_label) < width - 1:
                self.add_str(line, col + 1, rate_label, curses.A_DIM)
        return line + 1