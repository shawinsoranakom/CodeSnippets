def construct_constants(constants_list_from_yaml: list[Any]) -> str:
    constants_list_part = []
    for constant_from_yaml in constants_list_from_yaml:
        convert_constant = None
        if isinstance(constant_from_yaml, str):
            # Add quotes if it's string
            convert_constant = f'"{constant_from_yaml}"'
        elif isinstance(constant_from_yaml, bool):
            convert_constant = "true" if constant_from_yaml else "false"
        elif constant_from_yaml is None:
            convert_constant = ""
        elif isinstance(constant_from_yaml, int):
            convert_constant = str(constant_from_yaml)
        else:
            raise ValueError(
                f"The type of {constant_from_yaml} is {type(constant_from_yaml)}. "
                "Please add change in construct_constants function in gen_mobile_upgraders.py."
            )
        constants_list_part.append(ONE_CONSTANT.substitute(constant=convert_constant))
    if len(constants_list_part) == 0:
        return CONSTANTS_LIST_EMPTY
    return CONSTANT_LIST.substitute(
        constant_list="".join(constants_list_part).lstrip("\n")
    )