def __init__(self, limit_value, message=None, offset=None):
        super().__init__(limit_value, message)
        if offset is not None:
            self.message = _(
                "Ensure this value is a multiple of step size %(limit_value)s, "
                "starting from %(offset)s, e.g. %(offset)s, %(valid_value1)s, "
                "%(valid_value2)s, and so on."
            )
        self.offset = offset