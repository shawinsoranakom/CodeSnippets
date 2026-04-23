def deconstruct(self):
        return (self.__module__ + "." + self.__class__.__name__, self.args, self.kwargs)