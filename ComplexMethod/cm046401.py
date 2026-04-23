def _display(self, final: bool = False) -> None:
        """Display progress bar."""
        if self.disable or (self.closed and not final):
            return

        current_time = time.time()
        dt = current_time - self.last_print_t
        dn = self.n - self.last_print_n

        if not final and not self._should_update(dt, dn):
            return

        # Calculate rate (avoid crazy numbers)
        if dt > self.MIN_RATE_CALC_INTERVAL:
            rate = dn / dt if dt else 0.0
            # Smooth rate for reasonable values, use raw rate for very high values
            if rate < self.MAX_SMOOTHED_RATE:
                self.last_rate = self.RATE_SMOOTHING_FACTOR * rate + (1 - self.RATE_SMOOTHING_FACTOR) * self.last_rate
                rate = self.last_rate
        else:
            rate = self.last_rate

        # At completion, use overall rate
        if self.total and self.n >= self.total:
            overall_elapsed = current_time - self.start_t
            if overall_elapsed > 0:
                rate = self.n / overall_elapsed

        # Update counters
        self.last_print_n = self.n
        self.last_print_t = current_time
        elapsed = current_time - self.start_t

        # Remaining time
        remaining_str = ""
        if self.total and 0 < self.n < self.total and elapsed > 0:
            est_rate = rate or (self.n / elapsed)
            remaining_str = f"<{self._format_time((self.total - self.n) / est_rate)}"

        # Numbers and percent
        if self.total:
            percent = (self.n / self.total) * 100
            n_str = self._format_num(self.n)
            t_str = self._format_num(self.total)
            if self.is_bytes and n_str[-2] == t_str[-2]:  # Collapse suffix only when identical (e.g. "5.4/5.4MB")
                n_str = n_str.rstrip("KMGTPB")
        else:
            percent = 0.0
            n_str, t_str = self._format_num(self.n), "?"

        elapsed_str = self._format_time(elapsed)
        rate_str = self._format_rate(rate) or (self._format_rate(self.n / elapsed) if elapsed > 0 else "")

        bar = self._generate_bar()

        # Compose progress line via f-strings (two shapes: with/without total)
        if self.total:
            if self.is_bytes and self.n >= self.total:
                # Completed bytes: show only final size
                progress_str = f"{self.desc}: {percent:.0f}% {bar} {t_str} {rate_str} {elapsed_str}"
            else:
                progress_str = (
                    f"{self.desc}: {percent:.0f}% {bar} {n_str}/{t_str} {rate_str} {elapsed_str}{remaining_str}"
                )
        else:
            progress_str = f"{self.desc}: {bar} {n_str} {rate_str} {elapsed_str}"

        # Write to output
        try:
            if self.noninteractive:
                # In non-interactive environments, avoid carriage return which creates empty lines
                self.file.write(progress_str)
            else:
                # In interactive terminals, use carriage return and clear line for updating display
                self.file.write(f"\r\033[K{progress_str}")
            self.file.flush()
        except Exception:
            pass