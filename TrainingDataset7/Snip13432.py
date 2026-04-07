def filter_function(self, func, **flags):
        return self.filter(func.__name__, func, **flags)