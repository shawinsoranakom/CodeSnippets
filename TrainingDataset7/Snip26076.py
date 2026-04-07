def assertEndsWith(self, first, second):
        if not first.endswith(second):
            # Use assertEqual() for failure message with diffs. If first value
            # is much longer than second, truncate start and prepend an
            # ellipsis.
            self.longMessage = True
            max_len = len(second) + self.START_END_EXTRA_CONTEXT
            end_of_first = (
                first
                if len(first) <= max_len
                else ("…" if isinstance(first, str) else b"...") + first[-max_len:]
            )
            self.assertEqual(
                end_of_first,
                second,
                "First string doesn't end with the second.",
            )