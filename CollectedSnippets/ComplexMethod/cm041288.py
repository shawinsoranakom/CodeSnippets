def dict_multi_values(elements: list | dict) -> dict[str, list[Any]]:
    """
    Return a dictionary with the original keys from the list of dictionary and the
    values are the list of values of the original dictionary.
    """
    result_dict = {}
    if isinstance(elements, dict):
        for key, value in elements.items():
            if isinstance(value, list):
                result_dict[key] = value
            else:
                result_dict[key] = [value]
    elif isinstance(elements, list):
        if isinstance(elements[0], list):
            for key, value in elements:
                if key in result_dict:
                    result_dict[key].append(value)
                else:
                    result_dict[key] = [value]
        else:
            result_dict[elements[0]] = elements[1:]
    return result_dict