def set_param(k, v):
        """Set the parameter."""
        nonlocal new_params

        new_params[k] = {}
        new_params[k]["name"] = k
        new_params[k]["type"] = (
            "text"
            if v.get("type") == "object"
            else "date" if "date" in v.get("format", "") else v.get("type", "text")
        )
        new_params[k]["title"] = v.get("title")
        new_params[k]["description"] = v.get("description")
        new_params[k]["default"] = v.get("default")
        new_params[k]["x-widget_config"] = v.get("x-widget_config", {})
        choices: list = (
            [{"label": c, "value": c} for c in v.get("choices", []) if c]
            if v.get("choices")
            else []
        )

        if isinstance(v, dict) and "anyOf" in v:
            param_types = []
            for item in v["anyOf"]:
                if "type" in item and item.get("type") != "null":
                    param_types.append(item["type"])
                if "enum" in item:
                    choices.extend({"label": c, "value": c} for c in item["enum"])

            if param_types:
                new_params[k]["type"] = (
                    "number"
                    if "number" in param_types
                    or "integer" in param_types
                    and "string" not in param_types
                    and "date" not in param_types
                    else (
                        "date"
                        if any(
                            "date" in sub_prop.get("format", "")
                            for sub_prop in v["anyOf"]
                            if isinstance(sub_prop, dict)
                        )
                        else "text"
                    )
                )
            else:
                new_params[k]["type"] = (
                    "text"
                    if v.get("type") == "object"
                    else (
                        "date"
                        if "date" in v.get("format", "")
                        else v.get("type", "text")
                    )
                )
        elif isinstance(v, dict) and "enum" in v:
            choices.extend({"label": c, "value": c} for c in v["enum"] if c)

        if choices:
            new_params[k]["options"] = {"custom": choices}