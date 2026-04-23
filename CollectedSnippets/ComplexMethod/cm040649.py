def update(self, current, values=None, finalize=None):
        """Updates the progress bar.

        Args:
            current: Index of current step.
            values: List of tuples: `(name, value_for_last_step)`. If `name` is
                in `stateful_metrics`, `value_for_last_step` will be displayed
                as-is. Else, an average of the metric over time will be
                displayed.
            finalize: Whether this is the last update for the progress bar. If
                `None`, defaults to `current >= self.target`.
        """
        if finalize is None:
            if self.target is None:
                finalize = False
            else:
                finalize = current >= self.target

        values = values or []
        for k, v in values:
            if k not in self._values_order:
                self._values_order.append(k)
            if k not in self.stateful_metrics:
                # In the case that progress bar doesn't have a target value in
                # the first epoch, both on_batch_end and on_epoch_end will be
                # called, which will cause 'current' and 'self._seen_so_far' to
                # have the same value. Force the minimal value to 1 here,
                # otherwise stateful_metric will be 0s.
                if finalize:
                    self._values[k] = [v, 1]
                else:
                    value_base = max(current - self._seen_so_far, 1)
                    if k not in self._values:
                        self._values[k] = [v * value_base, value_base]
                    else:
                        self._values[k][0] += v * value_base
                        self._values[k][1] += value_base
            else:
                # Stateful metrics output a numeric value. This representation
                # means "take an average from a single value" but keeps the
                # numeric formatting.
                self._values[k] = [v, 1]
        self._seen_so_far = current

        message = ""
        special_char_len = 0
        now = time.time()
        time_per_unit = self._estimate_step_duration(current, now)

        if self.verbose == 1:
            if now - self._last_update < self.interval and not finalize:
                return

            if self._dynamic_display:
                message += "\b" * self._prev_total_width
                message += "\r"
            else:
                message += "\n"

            if self.target is not None and self.target > 0:
                numdigits = int(math.log10(self.target)) + 1
                bar = (f"%{numdigits}d/%d") % (current, self.target)
                bar = f"\x1b[1m{bar}\x1b[0m "
                special_char_len += 8
                prog = float(current) / self.target
                prog_width = int(self.width * prog)

                if prog_width > 0:
                    bar += f"\33[32m{'━' * prog_width}\x1b[0m"
                    special_char_len += 9
                bar += f"\33[37m{'━' * (self.width - prog_width)}\x1b[0m"
                special_char_len += 9

            else:
                bar = "%7d/Unknown" % current
            message += bar

            # Add ETA if applicable
            if self.target is not None and self.target > 0 and not finalize:
                eta = time_per_unit * (self.target - current)
                if eta > 3600:
                    eta_format = "%d:%02d:%02d" % (
                        eta // 3600,
                        (eta % 3600) // 60,
                        eta % 60,
                    )
                elif eta > 60:
                    eta_format = "%d:%02d" % (eta // 60, eta % 60)
                else:
                    eta_format = "%ds" % eta
                info = f" \x1b[1m{eta_format}\x1b[0m"
            else:
                # Time elapsed since start, in seconds
                info = f" \x1b[1m{now - self._start:.0f}s\x1b[0m"
            special_char_len += 8

            # Add time/step
            info += self._format_time(time_per_unit, self.unit_name)

            # Add metrics
            for k in self._values_order:
                info += f" - {k}:"
                if isinstance(self._values[k], list):
                    values, count = self._values[k]
                    if not isinstance(values, float):
                        values = np.mean(values)
                    avg = values / max(1, count)
                    if abs(avg) > 1e-3:
                        info += f" {avg:.4f}"
                    else:
                        info += f" {avg:.4e}"
                else:
                    info += f" {self._values[k]}"
            message += info

            total_width = len(bar) + len(info) - special_char_len
            if self._prev_total_width > total_width:
                message += " " * (self._prev_total_width - total_width)
            if finalize:
                message += "\n"

            io_utils.print_msg(message, line_break=False)
            self._prev_total_width = total_width
            message = ""

        elif self.verbose == 2:
            if finalize and self.target is not None and self.target > 0:
                numdigits = int(math.log10(self.target)) + 1
                count = f"%{numdigits}d/%d" % (current, self.target)
                info = f"{count} - {now - self._start:.0f}s"
                info += f" -{self._format_time(time_per_unit, self.unit_name)}"
                for k in self._values_order:
                    info += f" - {k}:"
                    values, count = self._values[k]
                    if not isinstance(values, float):
                        values = np.mean(values)
                    avg = values / max(1, count)
                    if avg > 1e-3:
                        info += f" {avg:.4f}"
                    else:
                        info += f" {avg:.4e}"
                info += "\n"
                message += info
                io_utils.print_msg(message, line_break=False)
                message = ""

        self._last_update = now