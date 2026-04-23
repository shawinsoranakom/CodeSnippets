def create_schema_from_function(
    model_name: str,
    func: Callable,
    *,
    filter_args: Sequence[str] | None = None,
    parse_docstring: bool = False,
    error_on_invalid_docstring: bool = False,
    include_injected: bool = True,
) -> type[BaseModel]:
    """Create a Pydantic schema from a function's signature.

    Args:
        model_name: Name to assign to the generated Pydantic schema.
        func: Function to generate the schema from.
        filter_args: Optional list of arguments to exclude from the schema.

            Defaults to `FILTERED_ARGS`.
        parse_docstring: Whether to parse the function's docstring for descriptions
            for each argument.
        error_on_invalid_docstring: If `parse_docstring` is provided, configure
            whether to raise `ValueError` on invalid Google Style docstrings.
        include_injected: Whether to include injected arguments in the schema.

            Defaults to `True`, since we want to include them in the schema when
            *validating* tool inputs.

    Returns:
        A Pydantic model with the same arguments as the function.
    """
    sig = inspect.signature(func)

    if _function_annotations_are_pydantic_v1(sig, func):
        validated = validate_arguments_v1(func, config=_SchemaConfig)  # type: ignore[call-overload]
    else:
        # https://docs.pydantic.dev/latest/usage/validation_decorator/
        with warnings.catch_warnings():
            # We are using deprecated functionality here.
            # This code should be re-written to simply construct a Pydantic model
            # using inspect.signature and create_model.
            warnings.simplefilter("ignore", category=PydanticDeprecationWarning)
            validated = validate_arguments(func, config=_SchemaConfig)  # type: ignore[operator]

    # Let's ignore `self` and `cls` arguments for class and instance methods
    # If qualified name has a ".", then it likely belongs in a class namespace
    in_class = bool(func.__qualname__ and "." in func.__qualname__)

    has_args = False
    has_kwargs = False

    for param in sig.parameters.values():
        if param.kind == param.VAR_POSITIONAL:
            has_args = True
        elif param.kind == param.VAR_KEYWORD:
            has_kwargs = True

    inferred_model = validated.model

    if filter_args:
        filter_args_ = filter_args
    else:
        # Handle classmethods and instance methods
        existing_params: list[str] = list(sig.parameters.keys())
        if existing_params and existing_params[0] in {"self", "cls"} and in_class:
            filter_args_ = [existing_params[0], *list(FILTERED_ARGS)]
        else:
            filter_args_ = list(FILTERED_ARGS)

        for existing_param in existing_params:
            if not include_injected and _is_injected_arg_type(
                sig.parameters[existing_param].annotation
            ):
                filter_args_.append(existing_param)

    description, arg_descriptions = _infer_arg_descriptions(
        func,
        parse_docstring=parse_docstring,
        error_on_invalid_docstring=error_on_invalid_docstring,
    )
    # Pydantic adds placeholder virtual fields we need to strip
    valid_properties = []
    for field in get_fields(inferred_model):
        if not has_args and field == "args":
            continue
        if not has_kwargs and field == "kwargs":
            continue

        if field == "v__duplicate_kwargs":  # Internal pydantic field
            continue

        if field not in filter_args_:
            valid_properties.append(field)

    return _create_subset_model(
        model_name,
        inferred_model,
        list(valid_properties),
        descriptions=arg_descriptions,
        fn_description=description,
    )