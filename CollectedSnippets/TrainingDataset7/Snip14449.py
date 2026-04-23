def __init__(self, func):
        self.real_func = func
        self.__doc__ = getattr(func, "__doc__")