def resolve_dependencies(d: dict, evaluated_conditions: dict[str, bool]) -> set[str]:
    items = set()

    if isinstance(d, dict):
        for k, v in d.items():
            if k == "Fn::If":
                # check the condition and only traverse down the correct path
                condition_name, true_value, false_value = v
                if evaluated_conditions[condition_name]:
                    items = items.union(resolve_dependencies(true_value, evaluated_conditions))
                else:
                    items = items.union(resolve_dependencies(false_value, evaluated_conditions))
            elif k == "Ref":
                items.add(v)
            elif k == "Fn::GetAtt":
                items.add(v[0] if isinstance(v, list) else v.split(".")[0])
            elif k == "Fn::Sub":
                # we can assume anything in there is a ref
                if isinstance(v, str):
                    # { "Fn::Sub" : "Hello ${Name}" }
                    variables_found = re.findall("\\${([^}]+)}", v)
                    for var in variables_found:
                        if "." in var:
                            var = var.split(".")[0]
                        items.add(var)
                elif isinstance(v, list):
                    # { "Fn::Sub" : [ "Hello ${Name}", { "Name": "SomeName" } ] }
                    variables_found = re.findall("\\${([^}]+)}", v[0])
                    for var in variables_found:
                        if var in v[1]:
                            # variable is included in provided mapping and can either be a static value or another reference
                            if isinstance(v[1][var], dict):
                                # e.g. { "Fn::Sub" : [ "Hello ${Name}", { "Name": {"Ref": "NameParam"} } ] }
                                #   the values can have references, so we need to go deeper
                                items = items.union(
                                    resolve_dependencies(v[1][var], evaluated_conditions)
                                )
                        else:
                            # it's now either a GetAtt call or a direct reference
                            if "." in var:
                                var = var.split(".")[0]
                            items.add(var)
                else:
                    raise Exception(f"Invalid template structure in Fn::Sub: {v}")
            elif isinstance(v, dict):
                items = items.union(resolve_dependencies(v, evaluated_conditions))
            elif isinstance(v, list):
                for item in v:
                    # TODO: assumption that every element is a dict might not be true
                    items = items.union(resolve_dependencies(item, evaluated_conditions))
            else:
                pass
    elif isinstance(d, list):
        for item in d:
            items = items.union(resolve_dependencies(item, evaluated_conditions))
    r = {i for i in items if not i.startswith("AWS::")}
    return r