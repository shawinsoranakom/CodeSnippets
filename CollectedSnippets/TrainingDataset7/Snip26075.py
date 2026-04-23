def assertStartsWith(self, first, second):
        if not first.startswith(second):
            # Use assertEqual() for failure message with diffs. If first value
            # is much longer than second, truncate end and add an ellipsis.
            self.longMessage = True
            max_len = len(second) + self.START_END_EXTRA_CONTEXT
            start_of_first = (
                first
                if len(first) <= max_len
                else first[:max_len] + ("…" if isinstance(first, str) else b"...")
            )
            self.assertEqual(
                start_of_first,
                second,
                "First string doesn't start with the second.",
            )