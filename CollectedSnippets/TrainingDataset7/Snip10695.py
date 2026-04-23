def __eq__(self, other):
        if isinstance(other, CheckConstraint):
            return (
                self.name == other.name
                and self.condition == other.condition
                and self.violation_error_code == other.violation_error_code
                and self.violation_error_message == other.violation_error_message
            )
        return super().__eq__(other)