def _recurse_list_properties(inner_list: list[Any]) -> str | None:
        list_properties: list[str | None] = []
        for item in inner_list:
            if item and isinstance(item, dict):
                list_properties.append(_recurse_properties(item))
            elif item and isinstance(item, list):
                list_properties.append(_recurse_list_properties(item))
            else:
                list_properties.append(str(item))
        return ", ".join([list_property for list_property in list_properties if list_property]) or None