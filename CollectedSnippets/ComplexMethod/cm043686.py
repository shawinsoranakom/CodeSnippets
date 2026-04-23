def replace_values_in_list_of_dicts(data):
    """Replace "NA" and "-" with None in a list of dictionaries."""
    for d in data:
        for k, v in d.items():
            if isinstance(v, dict):
                replace_values_in_list_of_dicts([v])  # Recurse into nested dictionary
            elif isinstance(v, list):
                for i in range(len(v)):  # pylint: disable=C0200
                    if isinstance(v[i], dict):
                        replace_values_in_list_of_dicts(
                            [v[i]]
                        )  # Recurse into nested dictionary in list
                    elif v[i] in ("NA", "-"):
                        v[i] = None  # Replace "NA" and "-" with None
            elif v in ("NA", "-"):
                d[k] = None  # Replace "NA" and "-" with None
    return data