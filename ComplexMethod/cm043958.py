def _extract_attribute_value(self, attr_value, attr_def):
        """Extract the actual value from an attribute."""
        if isinstance(attr_value, int):
            # Value is an index into the values array
            if "values" in attr_def and attr_value < len(attr_def["values"]):
                value_obj = attr_def["values"][attr_value]
                if isinstance(value_obj, dict):
                    return (
                        value_obj.get("en")
                        or value_obj.get("name")
                        or value_obj.get("id")
                    )
                return value_obj
        elif isinstance(attr_value, list) and attr_value:
            first_val = attr_value[0]
            if (
                isinstance(first_val, int)
                and "values" in attr_def
                and first_val < len(attr_def["values"])
            ):
                value_obj = attr_def["values"][first_val]
                if isinstance(value_obj, dict):
                    return (
                        value_obj.get("en")
                        or value_obj.get("name")
                        or value_obj.get("id")
                    )
                return value_obj
            if isinstance(first_val, dict):
                return first_val.get("en") or first_val.get("name") or first_val
            return first_val
        elif isinstance(attr_value, dict):
            return attr_value.get("en") or attr_value.get("name") or attr_value

        return attr_value