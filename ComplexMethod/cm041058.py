def expand_fn_foreach(
    foreach_defn: list,
    resolve_context: ResolveRefsRecursivelyContext,
    extra_replace_mapping: dict | None = None,
) -> dict:
    if len(foreach_defn) != 3:
        raise ValidationError(
            f"Fn::ForEach: invalid number of arguments, expected 3 got {len(foreach_defn)}"
        )
    output = {}
    iteration_name, iteration_value, template = foreach_defn
    if not isinstance(iteration_name, str):
        raise ValidationError(
            f"Fn::ForEach: incorrect type for iteration name '{iteration_name}', expected str"
        )
    if isinstance(iteration_value, dict):
        # we have a reference
        if "Ref" in iteration_value:
            iteration_value = resolve_context.resolve(iteration_value)
        else:
            raise NotImplementedError(
                f"Fn::Transform: intrinsic {iteration_value} not supported in this position yet"
            )
    if not isinstance(iteration_value, list):
        raise ValidationError(
            f"Fn::ForEach: incorrect type for iteration variables '{iteration_value}', expected list"
        )

    if not isinstance(template, dict):
        raise ValidationError(
            f"Fn::ForEach: incorrect type for template '{template}', expected dict"
        )

    # TODO: locations other than resources
    replace_template_value = "${" + iteration_name + "}"
    for variable in iteration_value:
        # there might be multiple children, which could themselves be a `Fn::ForEach` call
        for logical_resource_id_template in template:
            if logical_resource_id_template.startswith("Fn::ForEach"):
                result = expand_fn_foreach(
                    template[logical_resource_id_template],
                    resolve_context,
                    {iteration_name: variable},
                )
                output.update(**result)
                continue

            if replace_template_value not in logical_resource_id_template:
                raise ValidationError("Fn::ForEach: no placeholder in logical resource id")

            def gen_visit(variable: str) -> Callable:
                def _visit(obj: Any, path: Any):
                    if isinstance(obj, dict) and "Ref" in obj:
                        ref_variable = obj["Ref"]
                        if ref_variable == iteration_name:
                            return variable
                    elif isinstance(obj, dict) and "Fn::Sub" in obj:
                        arguments = recurse_object(obj["Fn::Sub"], _visit)
                        if isinstance(arguments, str):
                            # simple case
                            # TODO: can this reference anything outside of the template?
                            result = arguments
                            variables_found = re.findall("\\${([^}]+)}", arguments)
                            for var in variables_found:
                                if var == iteration_name:
                                    result = result.replace(f"${{{var}}}", variable)
                            return result
                        else:
                            raise NotImplementedError
                    elif isinstance(obj, dict) and "Fn::Join" in obj:
                        # first visit arguments
                        arguments = recurse_object(
                            obj["Fn::Join"],
                            _visit,
                        )
                        separator, items = arguments
                        return separator.join(items)
                    return obj

                return _visit

            logical_resource_id = logical_resource_id_template.replace(
                replace_template_value, variable
            )
            for key, value in (extra_replace_mapping or {}).items():
                logical_resource_id = logical_resource_id.replace("${" + key + "}", value)
            resource_body = copy.deepcopy(template[logical_resource_id_template])
            body = recurse_object(resource_body, gen_visit(variable))
            output[logical_resource_id] = body

    return output