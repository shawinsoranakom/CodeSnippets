def deconstruct(self):
        return (self.__class__.__qualname__, [self.name, self.managers], {})