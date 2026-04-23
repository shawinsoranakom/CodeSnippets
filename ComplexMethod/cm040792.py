def _validate_numeric_condition(self, value):
        if not value:
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Invalid member in numeric match: ]"
            )
        num_values = value[::-1]

        operator = num_values.pop()
        if not isinstance(operator, str):
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Invalid member in numeric match: {operator}"
            )
        elif operator not in ("<", "<=", "=", ">", ">="):
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Unrecognized numeric range operator: {operator}"
            )

        value = num_values.pop() if num_values else None
        if not isinstance(value, (int, float)):
            exc_operator = "equals" if operator == "=" else operator
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Value of {exc_operator} must be numeric"
            )

        if not num_values:
            return

        if operator not in (">", ">="):
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Too many elements in numeric expression"
            )

        second_operator = num_values.pop()
        if not isinstance(second_operator, str):
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Bad value in numeric range: {second_operator}"
            )
        elif second_operator not in ("<", "<="):
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Bad numeric range operator: {second_operator}"
            )

        second_value = num_values.pop() if num_values else None
        if not isinstance(second_value, (int, float)):
            exc_operator = "equals" if second_operator == "=" else second_operator
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Value of {exc_operator} must be numeric"
            )

        elif second_value <= value:
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Bottom must be less than top"
            )

        elif num_values:
            raise InvalidParameterException(
                f"{self.error_prefix}FilterPolicy: Too many terms in numeric range expression"
            )