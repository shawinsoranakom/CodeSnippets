def islice(iterable, *args):
        # islice('ABCDEFG', 2) → A B
        # islice('ABCDEFG', 2, 4) → C D
        # islice('ABCDEFG', 2, None) → C D E F G
        # islice('ABCDEFG', 0, None, 2) → A C E G

        s = slice(*args)
        start = 0 if s.start is None else s.start
        stop = s.stop
        step = 1 if s.step is None else s.step
        if start < 0 or (stop is not None and stop < 0) or step <= 0:
            raise ValueError

        indices = count() if stop is None else range(max(start, stop))
        next_i = start
        for i, element in zip(indices, iterable):
            if i == next_i:
                yield element
                next_i += step