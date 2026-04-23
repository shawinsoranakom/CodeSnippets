def resolve_condition(
    account_id: str, region_name: str, condition, conditions, parameters, mappings, stack_name
):
    if isinstance(condition, dict):
        for k, v in condition.items():
            match k:
                case "Ref":
                    if isinstance(v, str) and v.startswith("AWS::"):
                        return resolve_pseudo_parameter(
                            account_id, region_name, v, stack_name
                        )  # TODO: this pseudo parameter resolving needs context(!)
                    # TODO: add util function for resolving individual refs (e.g. one util for resolving pseudo parameters)
                    # TODO: pseudo-parameters like AWS::Region
                    # can only really be a parameter here
                    # TODO: how are conditions references written here? as {"Condition": "ConditionA"} or via Ref?
                    # TODO: test for a boolean parameter?
                    param = parameters[v]
                    parameter_type: str = param["ParameterType"]
                    parameter_value = param.get("ResolvedValue") or param.get("ParameterValue")

                    if parameter_type in ["CommaDelimitedList"] or parameter_type.startswith(
                        "List<"
                    ):
                        return [p.strip() for p in parameter_value.split(",")]
                    else:
                        return parameter_value

                case "Condition":
                    return resolve_condition(
                        account_id,
                        region_name,
                        conditions[v],
                        conditions,
                        parameters,
                        mappings,
                        stack_name,
                    )
                case "Fn::FindInMap":
                    map_name, top_level_key, second_level_key = v
                    if isinstance(map_name, dict) and "Ref" in map_name:
                        ref_name = map_name["Ref"]
                        map_name = resolve_conditional_mapping_ref(
                            ref_name, account_id, region_name, stack_name, parameters
                        )

                    if isinstance(top_level_key, dict) and "Ref" in top_level_key:
                        ref_name = top_level_key["Ref"]
                        top_level_key = resolve_conditional_mapping_ref(
                            ref_name, account_id, region_name, stack_name, parameters
                        )

                    if isinstance(second_level_key, dict) and "Ref" in second_level_key:
                        ref_name = second_level_key["Ref"]
                        second_level_key = resolve_conditional_mapping_ref(
                            ref_name, account_id, region_name, stack_name, parameters
                        )

                    mapping = mappings.get(map_name)
                    if not mapping:
                        raise TemplateError(
                            f"Invalid reference: '{map_name}' could not be found in the template mappings: '{list(mappings.keys())}'"
                        )

                    top_level_map = mapping.get(top_level_key)
                    if not top_level_map:
                        raise TemplateError(
                            f"Invalid reference: '{top_level_key}' could not be found in the '{map_name}' mapping: '{list(mapping.keys())}'"
                        )

                    value = top_level_map.get(second_level_key)
                    if not value:
                        raise TemplateError(
                            f"Invalid reference: '{second_level_key}' could not be found in the '{top_level_key}' mapping: '{top_level_map}'"
                        )

                    return value
                case "Fn::If":
                    if_condition_name, true_branch, false_branch = v
                    if resolve_condition(
                        account_id,
                        region_name,
                        if_condition_name,
                        conditions,
                        parameters,
                        mappings,
                        stack_name,
                    ):
                        return resolve_condition(
                            account_id,
                            region_name,
                            true_branch,
                            conditions,
                            parameters,
                            mappings,
                            stack_name,
                        )
                    else:
                        return resolve_condition(
                            account_id,
                            region_name,
                            false_branch,
                            conditions,
                            parameters,
                            mappings,
                            stack_name,
                        )
                case "Fn::Not":
                    return not resolve_condition(
                        account_id, region_name, v[0], conditions, parameters, mappings, stack_name
                    )
                case "Fn::And":
                    # TODO: should actually restrict this a bit
                    return resolve_condition(
                        account_id, region_name, v[0], conditions, parameters, mappings, stack_name
                    ) and resolve_condition(
                        account_id, region_name, v[1], conditions, parameters, mappings, stack_name
                    )
                case "Fn::Or":
                    return resolve_condition(
                        account_id, region_name, v[0], conditions, parameters, mappings, stack_name
                    ) or resolve_condition(
                        account_id, region_name, v[1], conditions, parameters, mappings, stack_name
                    )
                case "Fn::Equals":
                    left = resolve_condition(
                        account_id, region_name, v[0], conditions, parameters, mappings, stack_name
                    )
                    right = resolve_condition(
                        account_id, region_name, v[1], conditions, parameters, mappings, stack_name
                    )
                    return fn_equals_type_conversion(left) == fn_equals_type_conversion(right)
                case "Fn::Join":
                    join_list = v[1]
                    if isinstance(v[1], dict):
                        join_list = resolve_condition(
                            account_id,
                            region_name,
                            v[1],
                            conditions,
                            parameters,
                            mappings,
                            stack_name,
                        )
                    result = v[0].join(
                        [
                            resolve_condition(
                                account_id,
                                region_name,
                                x,
                                conditions,
                                parameters,
                                mappings,
                                stack_name,
                            )
                            for x in join_list
                        ]
                    )
                    return result
                case "Fn::Select":
                    index = v[0]
                    options = v[1]

                    if isinstance(options, dict):
                        options = resolve_condition(
                            account_id,
                            region_name,
                            options,
                            conditions,
                            parameters,
                            mappings,
                            stack_name,
                        )

                    if isinstance(options, list):
                        for i, option in enumerate(options):
                            if isinstance(option, dict):
                                options[i] = resolve_condition(
                                    account_id,
                                    region_name,
                                    option,
                                    conditions,
                                    parameters,
                                    mappings,
                                    stack_name,
                                )

                        return options[index]

                    if index != 0:
                        raise Exception(
                            f"Template error: Fn::Select  cannot select nonexistent value at index {index}"
                        )

                    return options

                case "Fn::Sub":
                    # we can assume anything in there is a ref
                    if isinstance(v, str):
                        # { "Fn::Sub" : "Hello ${Name}" }
                        result = v
                        variables_found = re.findall("\\${([^}]+)}", v)
                        for var in variables_found:
                            # can't be a resource here (!), so also not attribute access
                            if var.startswith("AWS::"):
                                # pseudo-parameter
                                resolved_pseudo_param = resolve_pseudo_parameter(
                                    account_id, region_name, var, stack_name
                                )
                                result = result.replace(f"${{{var}}}", resolved_pseudo_param)
                            else:
                                # parameter
                                param = parameters[var]
                                parameter_type: str = param["ParameterType"]
                                resolved_parameter = param.get("ResolvedValue") or param.get(
                                    "ParameterValue"
                                )

                                if parameter_type in [
                                    "CommaDelimitedList"
                                ] or parameter_type.startswith("List<"):
                                    resolved_parameter = [
                                        p.strip() for p in resolved_parameter.split(",")
                                    ]

                                result = result.replace(f"${{{var}}}", resolved_parameter)

                        return result
                    elif isinstance(v, list):
                        # { "Fn::Sub" : [ "Hello ${Name}", { "Name": "SomeName" } ] }
                        result = v[0]
                        variables_found = re.findall("\\${([^}]+)}", v[0])
                        for var in variables_found:
                            if var in v[1]:
                                # variable is included in provided mapping and can either be a static value or another reference
                                if isinstance(v[1][var], dict):
                                    # e.g. { "Fn::Sub" : [ "Hello ${Name}", { "Name": {"Ref": "NameParam"} } ] }
                                    #   the values can have references, so we need to go deeper
                                    resolved_var = resolve_condition(
                                        account_id,
                                        region_name,
                                        v[1][var],
                                        conditions,
                                        parameters,
                                        mappings,
                                        stack_name,
                                    )
                                    result = result.replace(f"${{{var}}}", resolved_var)
                                else:
                                    result = result.replace(f"${{{var}}}", v[1][var])
                            else:
                                # it's now either a GetAtt call or a direct reference
                                if var.startswith("AWS::"):
                                    # pseudo-parameter
                                    resolved_pseudo_param = resolve_pseudo_parameter(
                                        account_id, region_name, var, stack_name
                                    )
                                    result = result.replace(f"${{{var}}}", resolved_pseudo_param)
                                else:
                                    # parameter
                                    param = parameters[var]
                                    parameter_type: str = param["ParameterType"]
                                    resolved_parameter = param.get("ResolvedValue") or param.get(
                                        "ParameterValue"
                                    )

                                    if parameter_type in [
                                        "CommaDelimitedList"
                                    ] or parameter_type.startswith("List<"):
                                        resolved_parameter = [
                                            p.strip() for p in resolved_parameter.split(",")
                                        ]

                                    result = result.replace(f"${{{var}}}", resolved_parameter)
                        return result
                    else:
                        raise Exception(f"Invalid template structure in Fn::Sub: {v}")
                case _:
                    raise Exception(f"Invalid condition structure encountered: {condition=}")
    else:
        return condition