def __init__(self, operation, name, forced_collector=None):
        self.operation = operation
        self.forced_collector = forced_collector
        self.__name__ = name