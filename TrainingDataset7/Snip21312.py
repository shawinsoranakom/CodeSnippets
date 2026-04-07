def __str__(self):
        return "%i, %s, %s" % (
            self.integer,
            "%.3f" % self.float if self.float is not None else None,
            "%.17f" % self.decimal_value if self.decimal_value is not None else None,
        )