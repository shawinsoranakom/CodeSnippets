def __init__(self, expr1, expr2, spheroid=None, **extra):
        expressions = [expr1, expr2]
        if spheroid is not None:
            self.spheroid = self._handle_param(spheroid, "spheroid", bool)
        super().__init__(*expressions, **extra)