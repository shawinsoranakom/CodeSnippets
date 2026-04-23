def normpath(path):
        """Normalize path, eliminating double slashes, etc."""
        path = os.fspath(path)
        if isinstance(path, bytes):
            sep = b'/'
            dot = b'.'
            dotdot = b'..'
        else:
            sep = '/'
            dot = '.'
            dotdot = '..'
        if not path:
            return dot
        _, initial_slashes, path = splitroot(path)
        comps = path.split(sep)
        new_comps = []
        for comp in comps:
            if not comp or comp == dot:
                continue
            if (comp != dotdot or (not initial_slashes and not new_comps) or
                 (new_comps and new_comps[-1] == dotdot)):
                new_comps.append(comp)
            elif new_comps:
                new_comps.pop()
        comps = new_comps
        path = initial_slashes + sep.join(comps)
        return path or dot