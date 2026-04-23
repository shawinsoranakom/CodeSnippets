def _validate_numeric_condition(self, value):
        if not isinstance(value, list):
            raise InvalidEventPatternException(
                f"{self.error_prefix}Value of numeric must be an array."
            )
        if not value:
            raise InvalidEventPatternException(
                f"{self.error_prefix}Invalid member in numeric match: ]"
            )
        num_values = value[::-1]

        operator = num_values.pop()
        if not isinstance(operator, str):
            raise InvalidEventPatternException(
                f"{self.error_prefix}Invalid member in numeric match: {operator}"
            )
        elif operator not in ("<", "<=", "=", ">", ">="):
            raise InvalidEventPatternException(
                f"{self.error_prefix}Unrecognized numeric range operator: {operator}"
            )

        value = num_values.pop() if num_values else None
        if not isinstance(value, (int, float)):
            exc_operator = "equals" if operator == "=" else operator
            raise InvalidEventPatternException(
                f"{self.error_prefix}Value of {exc_operator} must be numeric"
            )

        if not num_values:
            return

        if operator not in (">", ">="):
            raise InvalidEventPatternException(
                f"{self.error_prefix}Too many elements in numeric expression"
            )

        second_operator = num_values.pop()
        if not isinstance(second_operator, str):
            raise InvalidEventPatternException(
                f"{self.error_prefix}Bad value in numeric range: {second_operator}"
            )
        elif second_operator not in ("<", "<="):
            raise InvalidEventPatternException(
                f"{self.error_prefix}Bad numeric range operator: {second_operator}"
            )

        second_value = num_values.pop() if num_values else None
        if not isinstance(second_value, (int, float)):
            exc_operator = "equals" if second_operator == "=" else second_operator
            raise InvalidEventPatternException(
                f"{self.error_prefix}Value of {exc_operator} must be numeric"
            )

        elif second_value <= value:
            raise InvalidEventPatternException(f"{self.error_prefix}Bottom must be less than top")

        elif num_values:
            raise InvalidEventPatternException(
                f"{self.error_prefix}Too many terms in numeric range expression"
            )