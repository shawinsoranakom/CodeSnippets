def validate_tool_names(tools: list[str]) -> dict[str, Tool]:
    assert isinstance(tools, list), "tools must be a list of str"
    valid_tools = {}
    for key in tools:
        # one can define either tool names OR tool tags OR tool path, take union to get the whole set
        # if tool paths are provided, they will be registered on the fly
        if os.path.isdir(key) or os.path.isfile(key):
            valid_tools.update(register_tools_from_path(key))
        elif TOOL_REGISTRY.has_tool(key.split(":")[0]):
            if ":" in key:
                # handle class tools with methods specified, such as Editor:read,write
                class_tool_name = key.split(":")[0]
                method_names = key.split(":")[1].split(",")
                class_tool = TOOL_REGISTRY.get_tool(class_tool_name)

                methods_filtered = {}
                for method_name in method_names:
                    if method_name in class_tool.schemas["methods"]:
                        methods_filtered[method_name] = class_tool.schemas["methods"][method_name]
                    else:
                        logger.warning(f"invalid method {method_name} under tool {class_tool_name}, skipped")
                class_tool_filtered = class_tool.model_copy(deep=True)
                class_tool_filtered.schemas["methods"] = methods_filtered

                valid_tools.update({class_tool_name: class_tool_filtered})

            else:
                valid_tools.update({key: TOOL_REGISTRY.get_tool(key)})
        elif TOOL_REGISTRY.has_tool_tag(key):
            valid_tools.update(TOOL_REGISTRY.get_tools_by_tag(key))
        else:
            logger.warning(f"invalid tool name or tool type name: {key}, skipped")
    return valid_tools