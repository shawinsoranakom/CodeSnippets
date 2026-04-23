def __eq__(self, other):
        if isinstance(other, UniqueConstraint):
            return (
                self.name == other.name
                and self.fields == other.fields
                and self.condition == other.condition
                and self.deferrable == other.deferrable
                and self.include == other.include
                and self.opclasses == other.opclasses
                and self.expressions == other.expressions
                and self.nulls_distinct is other.nulls_distinct
                and self.violation_error_code == other.violation_error_code
                and self.violation_error_message == other.violation_error_message
            )
        return super().__eq__(other)