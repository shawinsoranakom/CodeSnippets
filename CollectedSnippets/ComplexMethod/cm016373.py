def get_input_data(inputs, class_def, unique_id, execution_list=None, dynprompt=None, extra_data={}):
    is_v3 = issubclass(class_def, _ComfyNodeInternal)
    v3_data: io.V3Data = {}
    hidden_inputs_v3 = {}
    valid_inputs = class_def.INPUT_TYPES()
    if is_v3:
        valid_inputs, hidden, v3_data = _io.get_finalized_class_inputs(valid_inputs, inputs)
    input_data_all = {}
    missing_keys = {}
    for x in inputs:
        input_data = inputs[x]
        _, input_category, input_info = get_input_info(class_def, x, valid_inputs)
        def mark_missing():
            missing_keys[x] = True
            input_data_all[x] = (None,)
        if is_link(input_data) and (not input_info or not input_info.get("rawLink", False)):
            input_unique_id = input_data[0]
            output_index = input_data[1]
            if execution_list is None:
                mark_missing()
                continue # This might be a lazily-evaluated input
            cached = execution_list.get_cache(input_unique_id, unique_id)
            if cached is None or cached.outputs is None:
                mark_missing()
                continue
            if output_index >= len(cached.outputs):
                mark_missing()
                continue
            obj = cached.outputs[output_index]
            input_data_all[x] = obj
        elif input_category is not None or (is_v3 and class_def.ACCEPT_ALL_INPUTS):
            input_data_all[x] = [input_data]

    if is_v3:
        if hidden is not None:
            if io.Hidden.prompt.name in hidden:
                hidden_inputs_v3[io.Hidden.prompt] = dynprompt.get_original_prompt() if dynprompt is not None else {}
            if io.Hidden.dynprompt.name in hidden:
                hidden_inputs_v3[io.Hidden.dynprompt] = dynprompt
            if io.Hidden.extra_pnginfo.name in hidden:
                hidden_inputs_v3[io.Hidden.extra_pnginfo] = extra_data.get('extra_pnginfo', None)
            if io.Hidden.unique_id.name in hidden:
                hidden_inputs_v3[io.Hidden.unique_id] = unique_id
            if io.Hidden.auth_token_comfy_org.name in hidden:
                hidden_inputs_v3[io.Hidden.auth_token_comfy_org] = extra_data.get("auth_token_comfy_org", None)
            if io.Hidden.api_key_comfy_org.name in hidden:
                hidden_inputs_v3[io.Hidden.api_key_comfy_org] = extra_data.get("api_key_comfy_org", None)
    else:
        if "hidden" in valid_inputs:
            h = valid_inputs["hidden"]
            for x in h:
                if h[x] == "PROMPT":
                    input_data_all[x] = [dynprompt.get_original_prompt() if dynprompt is not None else {}]
                if h[x] == "DYNPROMPT":
                    input_data_all[x] = [dynprompt]
                if h[x] == "EXTRA_PNGINFO":
                    input_data_all[x] = [extra_data.get('extra_pnginfo', None)]
                if h[x] == "UNIQUE_ID":
                    input_data_all[x] = [unique_id]
                if h[x] == "AUTH_TOKEN_COMFY_ORG":
                    input_data_all[x] = [extra_data.get("auth_token_comfy_org", None)]
                if h[x] == "API_KEY_COMFY_ORG":
                    input_data_all[x] = [extra_data.get("api_key_comfy_org", None)]
    v3_data["hidden_inputs"] = hidden_inputs_v3
    return input_data_all, missing_keys, v3_data