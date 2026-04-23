def __init__(self, obj, subscript):
        super().__init__(obj.name)
        self.obj = obj
        if isinstance(subscript, int):
            if subscript < 0:
                raise ValueError("Negative indexing is not supported.")
            self.start = subscript + 1
            self.length = 1
        elif isinstance(subscript, slice):
            if (subscript.start is not None and subscript.start < 0) or (
                subscript.stop is not None and subscript.stop < 0
            ):
                raise ValueError("Negative indexing is not supported.")
            if subscript.step is not None:
                raise ValueError("Step argument is not supported.")
            if subscript.stop and subscript.start and subscript.stop < subscript.start:
                raise ValueError("Slice stop must be greater than slice start.")
            self.start = 1 if subscript.start is None else subscript.start + 1
            if subscript.stop is None:
                self.length = None
            else:
                self.length = subscript.stop - (subscript.start or 0)
        else:
            raise TypeError("Argument to slice must be either int or slice instance.")