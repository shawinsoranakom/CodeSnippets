def __init__(self, start=None, end=None, exclusion=None):
        self.start = Value(start)
        self.end = Value(end)
        if not isinstance(exclusion, (NoneType, WindowFrameExclusion)):
            raise TypeError(
                f"{self.__class__.__qualname__}.exclusion must be a "
                "WindowFrameExclusion instance."
            )
        self.exclusion = exclusion