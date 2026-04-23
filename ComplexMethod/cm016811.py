def validate_inputs(input_types):
                inputs = cls.INPUT_TYPES()
                for key, value in input_types.items():
                    if isinstance(value, SmartType):
                        continue
                    if "required" in inputs and key in inputs["required"]:
                        expected_type = inputs["required"][key][0]
                    elif "optional" in inputs and key in inputs["optional"]:
                        expected_type = inputs["optional"][key][0]
                    else:
                        expected_type = None
                    if expected_type is not None and MakeSmartType(value) != expected_type:
                        return f"Invalid type of {key}: {value} (expected {expected_type})"
                return True