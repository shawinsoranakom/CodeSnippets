def __init__(self, model_name, constraint):
        if not isinstance(constraint, CheckConstraint):
            raise TypeError(
                "AddConstraintNotValid.constraint must be a check constraint."
            )
        super().__init__(model_name, constraint)