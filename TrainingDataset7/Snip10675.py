def __init__(
        self, *, name, violation_error_code=None, violation_error_message=None
    ):
        self.name = name
        if violation_error_code is not None:
            self.violation_error_code = violation_error_code
        if violation_error_message is not None:
            self.violation_error_message = violation_error_message
        else:
            self.violation_error_message = self.default_violation_error_message