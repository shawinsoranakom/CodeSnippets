def _evaluate_numeric_condition(conditions: list, value: t.Any) -> bool:
        if not isinstance(value, (int, float)):
            return False
        try:
            # try if the value is numeric
            value = float(value)
        except ValueError:
            # the value is not numeric, the condition is False
            return False

        for i in range(0, len(conditions), 2):
            operator = conditions[i]
            operand = float(conditions[i + 1])

            if operator == "=":
                if value != operand:
                    return False
            elif operator == ">":
                if value <= operand:
                    return False
            elif operator == "<":
                if value >= operand:
                    return False
            elif operator == ">=":
                if value < operand:
                    return False
            elif operator == "<=":
                if value > operand:
                    return False

        return True