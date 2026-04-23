def create_simple_eg():
    excs = []
    try:
        try:
            raise MemoryError("context and cause for ValueError(1)")
        except MemoryError as e:
            raise ValueError(1) from e
    except ValueError as e:
        excs.append(e)

    try:
        try:
            raise OSError("context for TypeError")
        except OSError as e:
            raise TypeError(int)
    except TypeError as e:
        excs.append(e)

    try:
        try:
            raise ImportError("context for ValueError(2)")
        except ImportError as e:
            raise ValueError(2)
    except ValueError as e:
        excs.append(e)

    try:
        raise ExceptionGroup('simple eg', excs)
    except ExceptionGroup as e:
        return e