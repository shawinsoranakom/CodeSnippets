def window_frame_rows_start_end(self, start=None, end=None):
        """
        Return SQL for start and end points in an OVER clause window frame.
        """
        if isinstance(start, int) and isinstance(end, int) and start > end:
            raise ValueError("start cannot be greater than end.")
        if start is not None and not isinstance(start, int):
            raise ValueError(
                f"start argument must be an integer, zero, or None, but got '{start}'."
            )
        if end is not None and not isinstance(end, int):
            raise ValueError(
                f"end argument must be an integer, zero, or None, but got '{end}'."
            )
        start_ = self.window_frame_value(start) or self.UNBOUNDED_PRECEDING
        end_ = self.window_frame_value(end) or self.UNBOUNDED_FOLLOWING
        return start_, end_