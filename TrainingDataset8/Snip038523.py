def _serialize_dataframe_arg(key: str, value: Any) -> SpecialArg:
    special_arg = SpecialArg()
    special_arg.key = key
    component_arrow.marshall(special_arg.arrow_dataframe.data, value)
    return special_arg