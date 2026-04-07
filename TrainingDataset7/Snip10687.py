def __init__(
        self,
        *,
        condition,
        name,
        violation_error_code=None,
        violation_error_message=None,
    ):
        self.condition = condition
        if not getattr(condition, "conditional", False):
            raise TypeError(
                "CheckConstraint.condition must be a Q instance or boolean expression."
            )
        super().__init__(
            name=name,
            violation_error_code=violation_error_code,
            violation_error_message=violation_error_message,
        )