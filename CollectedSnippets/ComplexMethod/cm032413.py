def end(self):
        if self._idx == -1:
            return True
        parent = self.get_parent()
        logical_operator = parent._param.logical_operator if hasattr(parent._param, "logical_operator") else "and"
        conditions = []
        for item in parent._param.loop_termination_condition:
            if not item.get("variable") or not item.get("operator"):
                raise ValueError("Loop condition is incomplete.")
            var = self._canvas.get_variable_value(item["variable"])
            operator = item["operator"]
            input_mode = item.get("input_mode", "constant")

            if input_mode == "variable":
                value = self._canvas.get_variable_value(item.get("value", ""))
            elif input_mode == "constant":
                value = item.get("value", "")
            else:
                raise ValueError("Invalid input mode.")
            conditions.append(self.evaluate_condition(var, operator, value))
        should_end = (
            all(conditions) if logical_operator == "and"
            else any(conditions) if logical_operator == "or"
            else None
        )
        if should_end is None:
            raise ValueError("Invalid logical operator,should be 'and' or 'or'.")

        if should_end:
            self._idx = -1
            return True

        return False