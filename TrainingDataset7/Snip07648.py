def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.name == other.name
                and self.index_type.lower() == other.index_type.lower()
                and self.expressions == other.expressions
                and self.condition == other.condition
                and self.deferrable == other.deferrable
                and self.include == other.include
                and self.violation_error_code == other.violation_error_code
                and self.violation_error_message == other.violation_error_message
            )
        return super().__eq__(other)