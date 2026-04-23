def _resolve_input_type(annotation: Any, *, required: bool) -> tuple[type[InputTypes], bool, list[Any] | None]:
    """Resolve a Pydantic annotation into a Langflow input type."""
    ann = annotation

    if isinstance(ann, UnionType):
        non_none_types = [t for t in get_args(ann) if t is not type(None)]
        if len(non_none_types) == 1:
            ann = non_none_types[0]

    is_list = False

    # Handle unparameterized list (e.g., coming from nullable array schemas)
    # Treat it as a list of strings for input purposes.
    if ann is list:
        is_list = True
        ann = str

    if get_origin(ann) is list:
        is_list = True
        ann = get_args(ann)[0]

    options: list[Any] | None = None
    if get_origin(ann) is Literal:
        options = list(get_args(ann))
        if options:
            ann = type(options[0])

    if get_origin(ann) is Union:
        non_none = [t for t in get_args(ann) if t is not type(None)]
        if len(non_none) == 1:
            ann = non_none[0]

    if get_origin(ann) is dict:
        ann = dict

    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return NestedDictInput, is_list, options

    if ann is dict and not required:
        return NestedDictInput, is_list, options

    if options is not None:
        return DropdownInput, is_list, options

    if ann is Any:
        return MessageTextInput, is_list, options

    try:
        return _convert_type_to_field_type[ann], is_list, options
    except KeyError as err:
        msg = f"Unsupported field type: {ann}"
        raise TypeError(msg) from err