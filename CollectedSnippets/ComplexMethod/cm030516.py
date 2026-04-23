def _print_realtime_stats(self):
        """Print real-time sampling statistics."""
        if len(self.sample_intervals) < 2:
            return

        # Calculate statistics on the Hz values (deque automatically maintains rolling window)
        hz_values = list(self.sample_intervals)
        mean_hz = statistics.mean(hz_values)
        min_hz = min(hz_values)
        max_hz = max(hz_values)

        # Calculate microseconds per sample for all metrics (1/Hz * 1,000,000)
        mean_us_per_sample = (1.0 / mean_hz) * 1_000_000 if mean_hz > 0 else 0
        min_us_per_sample = (
            (1.0 / max_hz) * 1_000_000 if max_hz > 0 else 0
        )  # Min time = Max Hz
        max_us_per_sample = (
            (1.0 / min_hz) * 1_000_000 if min_hz > 0 else 0
        )  # Max time = Min Hz

        # Build cache stats string if stats collection is enabled
        cache_stats_str = ""
        if self.collect_stats:
            try:
                stats = self.unwinder.get_stats()
                hits = stats.get('frame_cache_hits', 0)
                partial = stats.get('frame_cache_partial_hits', 0)
                misses = stats.get('frame_cache_misses', 0)
                total = hits + partial + misses
                if total > 0:
                    hit_pct = (hits + partial) / total * 100
                    cache_stats_str = f" {ANSIColors.MAGENTA}Cache: {fmt(hit_pct)}% ({hits}+{partial}/{misses}){ANSIColors.RESET}"
            except RuntimeError:
                pass

        # Clear line and print stats
        print(
            f"\r\033[K{ANSIColors.BOLD_BLUE}Stats:{ANSIColors.RESET} "
            f"{ANSIColors.YELLOW}{fmt(mean_hz)}Hz ({fmt(mean_us_per_sample)}µs){ANSIColors.RESET} "
            f"{ANSIColors.GREEN}Min: {fmt(min_hz)}Hz{ANSIColors.RESET} "
            f"{ANSIColors.RED}Max: {fmt(max_hz)}Hz{ANSIColors.RESET} "
            f"{ANSIColors.CYAN}N={self.total_samples}{ANSIColors.RESET}"
            f"{cache_stats_str}",
            end="",
            flush=True,
        )