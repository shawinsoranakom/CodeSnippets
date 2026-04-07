def __init__(self, expression, delimiter, **extra):
        self.delimiter = StringAggDelimiter(delimiter)
        super().__init__(expression, self.delimiter, **extra)