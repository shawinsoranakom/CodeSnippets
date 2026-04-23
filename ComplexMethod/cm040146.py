def _set_interpreter_inputs(interpreter, inputs):
    input_details = interpreter.get_input_details()
    if isinstance(inputs, dict):
        for detail in input_details:
            key = _normalize_name(detail["name"])
            if key in inputs:
                value = inputs[key]
            else:
                matched_key = None
                for candidate in inputs:
                    if key.endswith(candidate) or candidate.endswith(key):
                        matched_key = candidate
                        break
                if matched_key is None:
                    raise KeyError(
                        f"Unable to match input '{detail['name']}' in provided "
                        f"inputs"
                    )
                value = inputs[matched_key]
            interpreter.set_tensor(detail["index"], value)
    else:
        values = inputs
        if not isinstance(values, (list, tuple)):
            values = [values]
        if len(values) != len(input_details):
            raise ValueError(
                "Number of provided inputs does not match interpreter signature"
            )
        for detail, value in zip(input_details, values):
            interpreter.set_tensor(detail["index"], value)