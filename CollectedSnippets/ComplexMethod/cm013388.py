def neg_step(i, s):
            if not (isinstance(s, slice) and s.step is not None and s.step < 0):
                return s

            nonlocal tensor
            tensor = torch.flip(tensor, (i,))

            # Account for the fact that a slice includes the start but not the end
            if not (isinstance(s.start, int) or s.start is None):
                raise AssertionError(
                    f"slice start must be int or None, got {type(s.start).__name__}"
                )
            if not (isinstance(s.stop, int) or s.stop is None):
                raise AssertionError(
                    f"slice stop must be int or None, got {type(s.stop).__name__}"
                )
            start = s.stop + 1 if s.stop else None
            stop = s.start + 1 if s.start else None

            return slice(start, stop, -s.step)