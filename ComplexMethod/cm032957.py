def _recurse_properties(inner_dict: dict[str, Any]) -> str | None:
        sub_inner_dict: dict[str, Any] | list[Any] | str = inner_dict
        while isinstance(sub_inner_dict, dict) and "type" in sub_inner_dict:
            type_name = sub_inner_dict["type"]
            sub_inner_dict = sub_inner_dict[type_name]

            if not sub_inner_dict:
                return None

        if isinstance(sub_inner_dict, list):
            return _recurse_list_properties(sub_inner_dict)
        elif isinstance(sub_inner_dict, str):
            return sub_inner_dict
        elif isinstance(sub_inner_dict, dict):
            if "name" in sub_inner_dict:
                return sub_inner_dict["name"]
            if "content" in sub_inner_dict:
                return sub_inner_dict["content"]
            start = sub_inner_dict.get("start")
            end = sub_inner_dict.get("end")
            if start is not None:
                if end is not None:
                    return f"{start} - {end}"
                return start
            elif end is not None:
                return f"Until {end}"

            if "id" in sub_inner_dict:
                logging.debug("Skipping Notion object id field property")
                return None

        logging.debug(f"Unreadable property from innermost prop: {sub_inner_dict}")
        return None