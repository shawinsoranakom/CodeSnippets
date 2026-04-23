def summary(self, decimal_places: int = 6, interval: int = 1) -> None:
        """Print a summary of step times.

        Parameters
        ----------
        decimal_places
            The number of decimal places to display the summary elapsed times to. Default: 6
        interval
            How many times summary must be called before printing to console. Default: 1

        Example
        -------
        >>> from lib.utils import DebugTimes
        >>> debug = DebugTimes()
        >>> debug.step_start("test")
        >>> time.sleep(0.5)
        >>> debug.step_end("test")
        >>> debug.summary()
        ----------------------------------
        Step             Count   Min
        ----------------------------------
        test             1       0.500000
        """
        interval = max(1, interval)
        if interval != self._interval:
            self._interval += 1
            return

        name_col = max(len(key) for key in self._times) + 4
        items_col = 8
        time_col = (decimal_places + 4) * sum(1 for v in self._display.values() if v)
        separator = "-" * (name_col + items_col + time_col)
        print("")
        print(separator)
        header = (f"{self._format_column('Step', name_col)}"
                  f"{self._format_column('Count', items_col)}")
        header += f"{self._format_column('Min', time_col)}" if self._display["min"] else ""
        header += f"{self._format_column('Avg', time_col)}" if self._display["mean"] else ""
        header += f"{self._format_column('Max', time_col)}" if self._display["max"] else ""
        print(header)
        print(separator)
        assert np is not None
        for key, val in self._times.items():
            num = str(len(val))
            contents = f"{self._format_column(key, name_col)}{self._format_column(num, items_col)}"
            if self._display["min"]:
                _min = f"{np.min(val):.{decimal_places}f}"
                contents += f"{self._format_column(_min, time_col)}"
            if self._display["mean"]:
                avg = f"{np.mean(val):.{decimal_places}f}"
                contents += f"{self._format_column(avg, time_col)}"
            if self._display["max"]:
                _max = f"{np.max(val):.{decimal_places}f}"
                contents += f"{self._format_column(_max, time_col)}"
            print(contents)
        self._interval = 1