async def validate_inputs(prompt_id, prompt, item, validated):
    unique_id = item
    if unique_id in validated:
        return validated[unique_id]

    inputs = prompt[unique_id]['inputs']
    class_type = prompt[unique_id]['class_type']
    obj_class = nodes.NODE_CLASS_MAPPINGS[class_type]

    errors = []
    valid = True

    v3_data = None
    validate_function_inputs = []
    validate_has_kwargs = False
    if issubclass(obj_class, _ComfyNodeInternal):
        obj_class: _io._ComfyNodeBaseInternal
        class_inputs = obj_class.INPUT_TYPES()
        class_inputs, _, v3_data = _io.get_finalized_class_inputs(class_inputs, inputs)
        validate_function_name = "validate_inputs"
        validate_function = first_real_override(obj_class, validate_function_name)
    else:
        class_inputs = obj_class.INPUT_TYPES()
        validate_function_name = "VALIDATE_INPUTS"
        validate_function = getattr(obj_class, validate_function_name, None)
    if validate_function is not None:
        argspec = inspect.getfullargspec(validate_function)
        validate_function_inputs = argspec.args
        validate_has_kwargs = argspec.varkw is not None
    received_types = {}

    valid_inputs = set(class_inputs.get('required',{})).union(set(class_inputs.get('optional',{})))

    for x in valid_inputs:
        input_type, input_category, extra_info = get_input_info(obj_class, x, class_inputs)
        assert extra_info is not None
        if x not in inputs:
            if input_category == "required":
                details = f"{x}" if not v3_data else x.split(".")[-1]
                error = {
                    "type": "required_input_missing",
                    "message": "Required input is missing",
                    "details": details,
                    "extra_info": {
                        "input_name": x
                    }
                }
                errors.append(error)
            continue

        val = inputs[x]
        info = (input_type, extra_info)
        if isinstance(val, list):
            if len(val) != 2:
                error = {
                    "type": "bad_linked_input",
                    "message": "Bad linked input, must be a length-2 list of [node_id, slot_index]",
                    "details": f"{x}",
                    "extra_info": {
                        "input_name": x,
                        "input_config": info,
                        "received_value": val
                    }
                }
                errors.append(error)
                continue

            o_id = val[0]
            o_class_type = prompt[o_id]['class_type']
            r = nodes.NODE_CLASS_MAPPINGS[o_class_type].RETURN_TYPES
            received_type = r[val[1]]
            received_types[x] = received_type
            if 'input_types' not in validate_function_inputs and not validate_node_input(received_type, input_type):
                details = f"{x}, received_type({received_type}) mismatch input_type({input_type})"
                error = {
                    "type": "return_type_mismatch",
                    "message": "Return type mismatch between linked nodes",
                    "details": details,
                    "extra_info": {
                        "input_name": x,
                        "input_config": info,
                        "received_type": received_type,
                        "linked_node": val
                    }
                }
                errors.append(error)
                continue
            try:
                r = await validate_inputs(prompt_id, prompt, o_id, validated)
                if r[0] is False:
                    # `r` will be set in `validated[o_id]` already
                    valid = False
                    continue
            except Exception as ex:
                typ, _, tb = sys.exc_info()
                valid = False
                exception_type = full_type_name(typ)
                reasons = [{
                    "type": "exception_during_inner_validation",
                    "message": "Exception when validating inner node",
                    "details": str(ex),
                    "extra_info": {
                        "input_name": x,
                        "input_config": info,
                        "exception_message": str(ex),
                        "exception_type": exception_type,
                        "traceback": traceback.format_tb(tb),
                        "linked_node": val
                    }
                }]
                validated[o_id] = (False, reasons, o_id)
                continue
        else:
            try:
                # Unwraps values wrapped in __value__ key or typed wrapper.
                # This is used to pass list widget values to execution,
                # as by default list value is reserved to represent the
                # connection between nodes.
                if isinstance(val, dict):
                    if "__value__" in val:
                        val = val["__value__"]
                        inputs[x] = val

                if input_type == "INT":
                    val = int(val)
                    inputs[x] = val
                if input_type == "FLOAT":
                    val = float(val)
                    inputs[x] = val
                if input_type == "STRING":
                    val = str(val)
                    inputs[x] = val
                if input_type == "BOOLEAN":
                    val = bool(val)
                    inputs[x] = val
            except Exception as ex:
                error = {
                    "type": "invalid_input_type",
                    "message": f"Failed to convert an input value to a {input_type} value",
                    "details": f"{x}, {val}, {ex}",
                    "extra_info": {
                        "input_name": x,
                        "input_config": info,
                        "received_value": val,
                        "exception_message": str(ex)
                    }
                }
                errors.append(error)
                continue

            if x not in validate_function_inputs and not validate_has_kwargs:
                if "min" in extra_info and val < extra_info["min"]:
                    error = {
                        "type": "value_smaller_than_min",
                        "message": "Value {} smaller than min of {}".format(val, extra_info["min"]),
                        "details": f"{x}",
                        "extra_info": {
                            "input_name": x,
                            "input_config": info,
                            "received_value": val,
                        }
                    }
                    errors.append(error)
                    continue
                if "max" in extra_info and val > extra_info["max"]:
                    error = {
                        "type": "value_bigger_than_max",
                        "message": "Value {} bigger than max of {}".format(val, extra_info["max"]),
                        "details": f"{x}",
                        "extra_info": {
                            "input_name": x,
                            "input_config": info,
                            "received_value": val,
                        }
                    }
                    errors.append(error)
                    continue

                if isinstance(input_type, list) or input_type == io.Combo.io_type:
                    if input_type == io.Combo.io_type:
                        combo_options = extra_info.get("options", [])
                    else:
                        combo_options = input_type
                    if val not in combo_options:
                        input_config = info
                        list_info = ""

                        # Don't send back gigantic lists like if they're lots of
                        # scanned model filepaths
                        if len(combo_options) > 20:
                            list_info = f"(list of length {len(combo_options)})"
                            input_config = None
                        else:
                            list_info = str(combo_options)

                        error = {
                            "type": "value_not_in_list",
                            "message": "Value not in list",
                            "details": f"{x}: '{val}' not in {list_info}",
                            "extra_info": {
                                "input_name": x,
                                "input_config": input_config,
                                "received_value": val,
                            }
                        }
                        errors.append(error)
                        continue

    if len(validate_function_inputs) > 0 or validate_has_kwargs:
        input_data_all, _, v3_data = get_input_data(inputs, obj_class, unique_id)
        input_filtered = {}
        for x in input_data_all:
            if x in validate_function_inputs or validate_has_kwargs:
                input_filtered[x] = input_data_all[x]
        if 'input_types' in validate_function_inputs:
            input_filtered['input_types'] = [received_types]

        ret = await _async_map_node_over_list(prompt_id, unique_id, obj_class, input_filtered, validate_function_name, v3_data=v3_data)
        ret = await resolve_map_node_over_list_results(ret)
        for x in input_filtered:
            for i, r in enumerate(ret):
                if r is not True and not isinstance(r, ExecutionBlocker):
                    details = f"{x}"
                    if r is not False:
                        details += f" - {str(r)}"

                    error = {
                        "type": "custom_validation_failed",
                        "message": "Custom validation failed for node",
                        "details": details,
                        "extra_info": {
                            "input_name": x,
                        }
                    }
                    errors.append(error)
                    continue

    if len(errors) > 0 or valid is not True:
        ret = (False, errors, unique_id)
    else:
        ret = (True, [], unique_id)

    validated[unique_id] = ret
    return ret