def _get_slice_indices(self, length: int, slice: slice) -> list[int]:
        step_is_negative = 0

        if slice.step is None:
            step = 1
            step_is_negative = False
        else:
            step = slice.step
            step_is_negative = slice.step < 0

        # Find lower and upper bounds for start and stop.
        if step_is_negative:
            lower = -1
            upper = length + lower
        else:
            lower = 0
            upper = length

        # Compute start
        if slice.start is None:
            start = upper if step_is_negative else lower
        else:
            start = slice.start

        if start < 0:
            start += length
            if start < lower:
                start = lower
        else:
            if start > upper:
                start = upper

        # Compute stop.
        if slice.stop is None:
            stop = lower if step_is_negative else upper

        else:
            stop = slice.stop

            if stop < 0:
                stop += length
                if stop < lower:
                    stop = lower
            else:
                if stop > upper:
                    stop = upper

        return [start, stop, step]