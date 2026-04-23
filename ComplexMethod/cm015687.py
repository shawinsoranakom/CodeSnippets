def islice(iterable, *args):
        s = slice(*args)
        start, stop, step = s.start or 0, s.stop or sys.maxsize, s.step or 1
        it = iter(range(start, stop, step))
        try:
            nexti = next(it)
        except StopIteration:
            # Consume *iterable* up to the *start* position.
            for i, element in zip(range(start), iterable):
                pass
            return
        try:
            for i, element in enumerate(iterable):
                if i == nexti:
                    yield element
                    nexti = next(it)
        except StopIteration:
            # Consume to *stop*.
            for i, element in zip(range(i + 1, stop), iterable):
                pass