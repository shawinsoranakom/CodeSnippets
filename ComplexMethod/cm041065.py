def _replace(match):
        ref_expression = match.group(1)
        parts = ref_expression.split(".")
        if len(parts) >= 2:
            # Resource attributes specified => Use GetAtt to resolve
            logical_resource_id, _, attr_name = ref_expression.partition(".")
            resolved = get_attr_from_model_instance(
                resources[logical_resource_id],
                attr_name,
                get_resource_type(resources[logical_resource_id]),
                logical_resource_id,
            )
            if resolved is None:
                raise DependencyNotYetSatisfied(
                    resource_ids=logical_resource_id,
                    message=f"Unable to resolve attribute ref {ref_expression}",
                )
            if not isinstance(resolved, str):
                resolved = str(resolved)
            return resolved
        if len(parts) == 1:
            if parts[0] in resources or parts[0].startswith("AWS::"):
                # Logical resource ID or parameter name specified => Use Ref for lookup
                result = resolve_ref(
                    account_id, region_name, stack_name, resources, parameters, parts[0]
                )

                if result is None:
                    raise DependencyNotYetSatisfied(
                        resource_ids=parts[0],
                        message=f"Unable to resolve attribute ref {ref_expression}",
                    )
                # TODO: is this valid?
                # make sure we resolve any functions/placeholders in the extracted string
                result = resolve_refs_recursively(
                    account_id,
                    region_name,
                    stack_name,
                    resources,
                    mappings,
                    conditions,
                    parameters,
                    result,
                )
                # make sure we convert the result to string
                # TODO: do this more systematically
                result = "" if result is None else str(result)
                return result
            elif parts[0] in parameters:
                parameter = parameters[parts[0]]
                parameter_type: str = parameter["ParameterType"]
                parameter_value = parameter.get("ResolvedValue") or parameter.get("ParameterValue")

                if parameter_type in ["CommaDelimitedList"] or parameter_type.startswith("List<"):
                    return [p.strip() for p in parameter_value.split(",")]
                elif parameter_type == "Number":
                    return str(parameter_value)
                else:
                    return parameter_value
            else:
                raise DependencyNotYetSatisfied(
                    resource_ids=parts[0],
                    message=f"Unable to resolve attribute ref {ref_expression}",
                )
        # TODO raise exception here?
        return match.group(0)