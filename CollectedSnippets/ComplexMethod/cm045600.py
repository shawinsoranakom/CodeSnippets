def assign_windows(instance: Any, key: TimeEventType):
            """Returns the list of all the windows the given key belongs to.

            Each window is a tuple (window_start, window_end) describing the range
            of the window (window_start inclusive, window_end exclusive).
            """
            # compute lower and upper bound for multipliers (first_k and last_k) of hop
            # for which corresponding windows could contain key.
            last_k = int((key - origin) // self.hop) + 1  # type: ignore[operator, arg-type]
            if self.ratio is not None:
                first_k = last_k - self.ratio - 1
            else:
                assert self.duration is not None
                first_k = last_k - int(self.duration // self.hop) - 1  # type: ignore[operator, arg-type]
            first_k -= 1  # safety to avoid off-by one

            candidate_windows = [
                kth_stable_window(k) for k in range(first_k, last_k + 1)
            ]

            # filtering below is needed to handle case when hop > duration
            return [
                (instance, start, end)
                for (start, end) in candidate_windows
                if start <= key
                and key < end
                and (self.origin is None or start >= self.origin)
            ]