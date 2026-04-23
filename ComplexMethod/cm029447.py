def _find_first_value_difference(
    left: JSONValue,
    right: JSONValue,
    path: str = "",
) -> tuple[str, JSONValue, JSONValue] | None:
    if type(left) is not type(right):
        return path, left, right

    if isinstance(left, dict):
        left_dict = _as_json_dict(left)
        right_dict = _as_json_dict(right)
        left_keys = list(left_dict.keys())
        right_keys = list(right_dict.keys())
        for index in range(min(len(left_keys), len(right_keys))):
            left_key = left_keys[index]
            right_key = right_keys[index]
            if left_key != right_key:
                key_path = _append_dict_path(path, left_key)
                return key_path, left, right

        if len(left_keys) != len(right_keys):
            extra_key = (
                left_keys[len(right_keys)]
                if len(left_keys) > len(right_keys)
                else right_keys[len(left_keys)]
            )
            key_path = _append_dict_path(path, extra_key)
            left_value = left_dict.get(extra_key)
            right_value = right_dict.get(extra_key)
            return key_path, cast(JSONValue, left_value), cast(JSONValue, right_value)

        for key in left_keys:
            nested = _find_first_value_difference(
                left_dict[key],
                right_dict[key],
                _append_dict_path(path, key),
            )
            if nested is not None:
                return nested
        return None

    if isinstance(left, list):
        left_list = _as_json_list(left)
        right_list = _as_json_list(right)
        for index in range(min(len(left_list), len(right_list))):
            nested = _find_first_value_difference(
                left_list[index],
                right_list[index],
                _append_list_path(path, index),
            )
            if nested is not None:
                return nested

        if len(left_list) != len(right_list):
            index = min(len(left_list), len(right_list))
            item_path = _append_list_path(path, index)
            left_value = left_list[index] if index < len(left_list) else None
            right_value = right_list[index] if index < len(right_list) else None
            return item_path, left_value, right_value
        return None

    if left != right:
        return path, left, right

    return None