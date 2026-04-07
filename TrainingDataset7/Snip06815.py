def __init__(self, expr1, spheroid=True, **extra):
        self.spheroid = spheroid
        super().__init__(expr1, **extra)