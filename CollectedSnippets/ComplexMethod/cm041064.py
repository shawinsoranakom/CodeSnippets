def _resolve_refs_recursively(
    account_id: str,
    region_name: str,
    stack_name: str,
    resources: dict,
    mappings: dict,
    conditions: dict,
    parameters: dict,
    value: dict | list | str | bytes | None,
):
    if isinstance(value, dict):
        keys_list = list(value.keys())
        stripped_fn_lower = keys_list[0].lower().split("::")[-1] if len(keys_list) == 1 else None

        # process special operators
        if keys_list == ["Ref"]:
            ref = resolve_ref(
                account_id, region_name, stack_name, resources, parameters, value["Ref"]
            )
            if ref is None:
                msg = 'Unable to resolve Ref for resource "{}" (yet)'.format(value["Ref"])
                LOG.debug("%s - %s", msg, resources.get(value["Ref"]) or set(resources.keys()))

                raise DependencyNotYetSatisfied(resource_ids=value["Ref"], message=msg)

            ref = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                ref,
            )
            return ref

        if stripped_fn_lower == "getatt":
            attr_ref = value[keys_list[0]]
            attr_ref = attr_ref.split(".") if isinstance(attr_ref, str) else attr_ref
            resource_logical_id = attr_ref[0]
            attribute_name = attr_ref[1]
            attribute_sub_name = attr_ref[2] if len(attr_ref) > 2 else None

            # the attribute name can be a Ref
            attribute_name = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                attribute_name,
            )
            resource = resources.get(resource_logical_id)

            resource_type = get_resource_type(resource)
            resolved_getatt = get_attr_from_model_instance(
                resource,
                attribute_name,
                resource_type,
                resource_logical_id,
                attribute_sub_name,
            )

            # TODO: we should check the deployment state and not try to GetAtt from a resource that is still IN_PROGRESS or hasn't started yet.
            if resolved_getatt is None:
                raise DependencyNotYetSatisfied(
                    resource_ids=resource_logical_id,
                    message=f"Could not resolve attribute '{attribute_name}' on resource '{resource_logical_id}'",
                )

            return resolved_getatt

        if stripped_fn_lower == "join":
            join_values = value[keys_list[0]][1]

            # this can actually be another ref that produces a list as output
            if isinstance(join_values, dict):
                join_values = resolve_refs_recursively(
                    account_id,
                    region_name,
                    stack_name,
                    resources,
                    mappings,
                    conditions,
                    parameters,
                    join_values,
                )

            # resolve reference in the items list
            assert isinstance(join_values, list)
            join_values = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                join_values,
            )

            none_values = [v for v in join_values if v is None]
            if none_values:
                LOG.warning(
                    "Cannot resolve Fn::Join '%s' due to null values: '%s'", value, join_values
                )
                raise Exception(
                    f"Cannot resolve CF Fn::Join {value} due to null values: {join_values}"
                )
            return value[keys_list[0]][0].join([str(v) for v in join_values])

        if stripped_fn_lower == "sub":
            item_to_sub = value[keys_list[0]]

            attr_refs = {r: {"Ref": r} for r in STATIC_REFS}
            if not isinstance(item_to_sub, list):
                item_to_sub = [item_to_sub, {}]
            result = item_to_sub[0]
            item_to_sub[1].update(attr_refs)

            for key, val in item_to_sub[1].items():
                resolved_val = resolve_refs_recursively(
                    account_id,
                    region_name,
                    stack_name,
                    resources,
                    mappings,
                    conditions,
                    parameters,
                    val,
                )

                if isinstance(resolved_val, (list, dict, tuple)):
                    # We don't have access to the resource that's a dependency in this case,
                    # so do the best we can with the resource ids
                    raise DependencyNotYetSatisfied(
                        resource_ids=key, message=f"Could not resolve {val} to terminal value type"
                    )
                result = result.replace(f"${{{key}}}", str(resolved_val))

            # resolve placeholders
            result = resolve_placeholders_in_string(
                account_id,
                region_name,
                result,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
            )
            return result

        if stripped_fn_lower == "findinmap":
            # "Fn::FindInMap"
            mapping_id = value[keys_list[0]][0]

            if isinstance(mapping_id, dict) and "Ref" in mapping_id:
                # TODO: ??
                mapping_id = resolve_ref(
                    account_id, region_name, stack_name, resources, parameters, mapping_id["Ref"]
                )

            selected_map = mappings.get(mapping_id)
            if not selected_map:
                raise Exception(
                    f"Cannot find Mapping with ID {mapping_id} for Fn::FindInMap: {value[keys_list[0]]} {list(resources.keys())}"
                    # TODO: verify
                )

            first_level_attribute = value[keys_list[0]][1]
            first_level_attribute = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                first_level_attribute,
            )

            if first_level_attribute not in selected_map:
                raise Exception(
                    f"Cannot find map key '{first_level_attribute}' in mapping '{mapping_id}'"
                )
            first_level_mapping = selected_map[first_level_attribute]

            second_level_attribute = value[keys_list[0]][2]
            if not isinstance(second_level_attribute, str):
                second_level_attribute = resolve_refs_recursively(
                    account_id,
                    region_name,
                    stack_name,
                    resources,
                    mappings,
                    conditions,
                    parameters,
                    second_level_attribute,
                )
            if second_level_attribute not in first_level_mapping:
                raise Exception(
                    f"Cannot find map key '{second_level_attribute}' in mapping '{mapping_id}' under key '{first_level_attribute}'"
                )

            return first_level_mapping[second_level_attribute]

        if stripped_fn_lower == "importvalue":
            import_value_key = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                value[keys_list[0]],
            )
            exports = exports_map(account_id, region_name)
            stack_export = exports.get(import_value_key) or {}
            if not stack_export.get("Value"):
                LOG.info(
                    'Unable to find export "%s" in stack "%s", existing export names: %s',
                    import_value_key,
                    stack_name,
                    list(exports.keys()),
                )
                return None
            return stack_export["Value"]

        if stripped_fn_lower == "if":
            condition, option1, option2 = value[keys_list[0]]
            condition = conditions.get(condition)
            if condition is None:
                LOG.warning(
                    "Cannot find condition '%s' in conditions mapping: '%s'",
                    condition,
                    conditions.keys(),
                )
                raise KeyError(
                    f"Cannot find condition '{condition}' in conditions mapping: '{conditions.keys()}'"
                )

            result = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                option1 if condition else option2,
            )
            return result

        if stripped_fn_lower == "condition":
            # FIXME: this should only allow strings, no evaluation should be performed here
            #   see https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-condition.html
            key = value[keys_list[0]]
            result = conditions.get(key)
            if result is None:
                LOG.warning("Cannot find key '%s' in conditions: '%s'", key, conditions.keys())
                raise KeyError(f"Cannot find key '{key}' in conditions: '{conditions.keys()}'")
            return result

        if stripped_fn_lower == "not":
            condition = value[keys_list[0]][0]
            condition = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                condition,
            )
            return not condition

        if stripped_fn_lower in ["and", "or"]:
            conditions = value[keys_list[0]]
            results = [
                resolve_refs_recursively(
                    account_id,
                    region_name,
                    stack_name,
                    resources,
                    mappings,
                    conditions,
                    parameters,
                    cond,
                )
                for cond in conditions
            ]
            result = all(results) if stripped_fn_lower == "and" else any(results)
            return result

        if stripped_fn_lower == "equals":
            operand1, operand2 = value[keys_list[0]]
            operand1 = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                operand1,
            )
            operand2 = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                operand2,
            )
            # TODO: investigate type coercion here
            return fn_equals_type_conversion(operand1) == fn_equals_type_conversion(operand2)

        if stripped_fn_lower == "select":
            index, values = value[keys_list[0]]
            index = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                index,
            )
            values = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                values,
            )
            try:
                return values[index]
            except TypeError:
                return values[int(index)]

        if stripped_fn_lower == "split":
            delimiter, string = value[keys_list[0]]
            delimiter = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                delimiter,
            )
            string = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                string,
            )
            return string.split(delimiter)

        if stripped_fn_lower == "getazs":
            region = (
                resolve_refs_recursively(
                    account_id,
                    region_name,
                    stack_name,
                    resources,
                    mappings,
                    conditions,
                    parameters,
                    value["Fn::GetAZs"],
                )
                or region_name
            )

            ec2_client = connect_to(aws_access_key_id=account_id, region_name=region).ec2
            try:
                get_availability_zones = ec2_client.describe_availability_zones()[
                    "AvailabilityZones"
                ]
            except ClientError:
                LOG.error("client error describing availability zones")
                raise

            azs = [az["ZoneName"] for az in get_availability_zones]

            return azs

        if stripped_fn_lower == "base64":
            value_to_encode = value[keys_list[0]]
            value_to_encode = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                value_to_encode,
            )
            return to_str(base64.b64encode(to_bytes(value_to_encode)))

        for key, val in dict(value).items():
            value[key] = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                val,
            )

    if isinstance(value, list):
        # in some cases, intrinsic functions are passed in as, e.g., `[['Fn::Sub', '${MyRef}']]`
        if len(value) == 1 and isinstance(value[0], list) and len(value[0]) == 2:
            inner_list = value[0]
            if str(inner_list[0]).lower().startswith("fn::"):
                return resolve_refs_recursively(
                    account_id,
                    region_name,
                    stack_name,
                    resources,
                    mappings,
                    conditions,
                    parameters,
                    {inner_list[0]: inner_list[1]},
                )

        # remove _aws_no_value_ from resulting references
        clean_list = []
        for item in value:
            temp_value = resolve_refs_recursively(
                account_id,
                region_name,
                stack_name,
                resources,
                mappings,
                conditions,
                parameters,
                item,
            )
            if not (isinstance(temp_value, str) and temp_value == PLACEHOLDER_AWS_NO_VALUE):
                clean_list.append(temp_value)
        value = clean_list

    return value