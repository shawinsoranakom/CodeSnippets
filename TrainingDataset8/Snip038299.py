def lower_clean_dict_keys(dict: Mapping[_Key, _Value]) -> Dict[str, _Value]:
    return {k.lower().strip(): v for k, v in dict.items()}