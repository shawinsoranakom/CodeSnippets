def _xml_to_function_call(invoke: Any, tools: list[dict]) -> dict[str, Any]:
    name = invoke.find("tool_name").text
    arguments = _xml_to_dict(invoke.find("parameters"))

    # make list elements in arguments actually lists
    filtered_tools = [tool for tool in tools if tool["name"] == name]
    if len(filtered_tools) > 0 and not isinstance(arguments, str):
        tool = filtered_tools[0]
        for key, value in arguments.items():
            if (
                key in tool["parameters"]["properties"]
                and "type" in tool["parameters"]["properties"][key]
            ):
                if tool["parameters"]["properties"][key][
                    "type"
                ] == "array" and not isinstance(value, list):
                    arguments[key] = [value]
                if (
                    tool["parameters"]["properties"][key]["type"] != "object"
                    and isinstance(value, dict)
                    and len(value.keys()) == 1
                ):
                    arguments[key] = next(iter(value.values()))

    return {
        "function": {
            "name": name,
            "arguments": json.dumps(arguments),
        },
        "type": "function",
    }