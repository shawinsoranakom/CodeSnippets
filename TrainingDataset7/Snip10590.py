def __init__(self, expression, sample=False, **extra):
        self.function = "VAR_SAMP" if sample else "VAR_POP"
        super().__init__(expression, **extra)