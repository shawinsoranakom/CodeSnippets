def opener(path, flags):
            nonlocal called
            called = True
            return os.open(path, flags)