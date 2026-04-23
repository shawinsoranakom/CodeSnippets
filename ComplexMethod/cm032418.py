def process_operator(self, input: Any, operator: str, value: Any) -> bool:
        if operator == "contains":
            return True if value.lower() in input.lower() else False
        elif operator == "not contains":
            return True if value.lower() not in input.lower() else False
        elif operator == "start with":
            return True if input.lower().startswith(value.lower()) else False
        elif operator == "end with":
            return True if input.lower().endswith(value.lower()) else False
        elif operator == "empty":
            return True if not input else False
        elif operator == "not empty":
            return True if input else False
        elif operator == "=":
            return True if input == value else False
        elif operator == "≠":
            return True if input != value else False
        elif operator == ">":
            try:
                return True if float(input) > float(value) else False
            except Exception:
                return True if input > value else False
        elif operator == "<":
            try:
                return True if float(input) < float(value) else False
            except Exception:
                return True if input < value else False
        elif operator == "≥":
            try:
                return True if float(input) >= float(value) else False
            except Exception:
                return True if input >= value else False
        elif operator == "≤":
            try:
                return True if float(input) <= float(value) else False
            except Exception:
                return True if input <= value else False

        raise ValueError(f'Not supported operator: {operator}')