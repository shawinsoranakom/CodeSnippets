def _expand_schema_for_dynamic(out_dict: dict[str, Any], live_inputs: dict[str, Any], value: tuple[str, dict[str, Any]], input_type: str, curr_prefix: list[str] | None):
        # NOTE: purposely do not include self in out_dict; instead use only the template inputs
        # need to figure out names based on template type
        is_names = ("names" in value[1]["template"])
        is_prefix = ("prefix" in value[1]["template"])
        input = value[1]["template"]["input"]
        if is_names:
            min = value[1]["template"]["min"]
            names = value[1]["template"]["names"]
            max = len(names)
        elif is_prefix:
            prefix = value[1]["template"]["prefix"]
            min = value[1]["template"]["min"]
            max = value[1]["template"]["max"]
            names = [f"{prefix}{i}" for i in range(max)]
        # need to create a new input based on the contents of input
        template_input = None
        template_required = True
        for _input_type, dict_input in input.items():
            # for now, get just the first value from dict_input; if not required, min can be ignored
            if len(dict_input) == 0:
                continue
            template_input = list(dict_input.values())[0]
            template_required = _input_type == "required"
            break
        if template_input is None:
            raise Exception("template_input could not be determined from required or optional; this should never happen.")
        new_dict = {}
        new_dict_added_to = False
        # first, add possible inputs into out_dict
        for i, name in enumerate(names):
            expected_id = finalize_prefix(curr_prefix, name)
            # required
            if i < min and template_required:
                out_dict["required"][expected_id] = template_input
                type_dict = new_dict.setdefault("required", {})
            # optional
            else:
                out_dict["optional"][expected_id] = template_input
                type_dict = new_dict.setdefault("optional", {})
            if expected_id in live_inputs:
                # NOTE: prefix gets added in parse_class_inputs
                type_dict[name] = template_input
                new_dict_added_to = True
        # account for the edge case that all inputs are optional and no values are received
        if not new_dict_added_to:
            finalized_prefix = finalize_prefix(curr_prefix)
            out_dict["dynamic_paths"][finalized_prefix] = finalized_prefix
            out_dict["dynamic_paths_default_value"][finalized_prefix] = DynamicPathsDefaultValue.EMPTY_DICT
        parse_class_inputs(out_dict, live_inputs, new_dict, curr_prefix)