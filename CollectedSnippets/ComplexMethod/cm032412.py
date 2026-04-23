def evaluate_condition(self,var, operator, value):
        if isinstance(var, str):
            if operator == "contains":
                return value in var
            elif operator == "not contains":
                return value not in var
            elif operator == "start with":
                return var.startswith(value)
            elif operator == "end with":
                return var.endswith(value)
            elif operator == "is":
                return var == value
            elif operator == "is not":
                return var != value
            elif operator == "empty":
                return var == ""
            elif operator == "not empty":
                return var != ""

        elif isinstance(var, (int, float)):
            if operator == "=":
                return var == value
            elif operator == "≠":
                return var != value
            elif operator == ">":
                return var > value
            elif operator == "<":
                return var < value
            elif operator == "≥":
                return var >= value
            elif operator == "≤":
                return var <= value
            elif operator == "empty":
                return var is None
            elif operator == "not empty":
                return var is not None

        elif isinstance(var, bool):
            if operator == "is":
                return var is value
            elif operator == "is not":
                return var is not value
            elif operator == "empty":
                return var is None
            elif operator == "not empty":
                return var is not None

        elif isinstance(var, dict):
            if operator == "empty":
                return len(var) == 0
            elif operator == "not empty":
                return len(var) > 0

        elif isinstance(var, list):
            if operator == "contains":
                return value in var
            elif operator == "not contains":
                return value not in var

            elif operator == "is":
                return var == value
            elif operator == "is not":
                return var != value

            elif operator == "empty":
                return len(var) == 0
            elif operator == "not empty":
                return len(var) > 0
        elif var is None:
            if operator == "empty":
                return True
            return False

        raise Exception(f"Invalid operator: {operator}")