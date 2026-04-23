def _evaluate_filter_policy_conditions_on_attribute(
        self, conditions, attribute, field_exists: bool
    ):
        if not isinstance(conditions, list):
            conditions = [conditions]

        tpe = attribute.get("DataType") or attribute.get("Type") if attribute else None
        val = attribute.get("StringValue") or attribute.get("Value") if attribute else None
        if attribute is not None and tpe == "String.Array":
            try:
                values = json.loads(val)
            except ValueError:
                return False
            for value in values:
                for condition in conditions:
                    if self._evaluate_condition(value, condition, field_exists):
                        return True
        else:
            for condition in conditions:
                value = val or None
                if self._evaluate_condition(value, condition, field_exists):
                    return True

        return False