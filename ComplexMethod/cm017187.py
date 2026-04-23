def window_frame_range_start_end(self, start=None, end=None):
        if (start is not None and not isinstance(start, int)) or (
            isinstance(start, int) and start > 0
        ):
            raise ValueError(
                "start argument must be a negative integer, zero, or None, "
                "but got '%s'." % start
            )
        if (end is not None and not isinstance(end, int)) or (
            isinstance(end, int) and end < 0
        ):
            raise ValueError(
                "end argument must be a positive integer, zero, or None, but got '%s'."
                % end
            )
        start_ = self.window_frame_value(start) or self.UNBOUNDED_PRECEDING
        end_ = self.window_frame_value(end) or self.UNBOUNDED_FOLLOWING
        features = self.connection.features
        if features.only_supports_unbounded_with_preceding_and_following and (
            (start and start < 0) or (end and end > 0)
        ):
            raise NotSupportedError(
                "%s only supports UNBOUNDED together with PRECEDING and "
                "FOLLOWING." % self.connection.display_name
            )
        return start_, end_