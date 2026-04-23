def create_model_v2(
    model_name: str,
    *,
    module_name: str | None = None,
    field_definitions: dict[str, Any] | None = None,
    root: Any | None = None,
) -> type[BaseModel]:
    """Create a Pydantic model with the given field definitions.

    !!! warning

        Do not use outside of langchain packages. This API is subject to change at any
        time.

    Args:
        model_name: The name of the model.
        module_name: The name of the module where the model is defined.

            This is used by Pydantic to resolve any forward references.
        field_definitions: The field definitions for the model.
        root: Type for a root model (`RootModel`)

    Returns:
        The created model.
    """
    field_definitions = field_definitions or {}

    if root:
        if field_definitions:
            msg = (
                "When specifying __root__ no other "
                f"fields should be provided. Got {field_definitions}"
            )
            raise NotImplementedError(msg)

        if isinstance(root, tuple):
            kwargs = {"type_": root[0], "default_": root[1]}
        else:
            kwargs = {"type_": root}

        try:
            named_root_model = _create_root_model_cached(
                model_name, module_name=module_name, **kwargs
            )
        except TypeError:
            # something in the arguments into _create_root_model_cached is not hashable
            named_root_model = _create_root_model(
                model_name,
                module_name=module_name,
                **kwargs,
            )
        return named_root_model

    # No root, just field definitions
    names = set(field_definitions.keys())

    capture_warnings = False

    for name in names:
        # Also if any non-reserved name is used (e.g., model_id or model_name)
        if name.startswith("model"):
            capture_warnings = True

    with warnings.catch_warnings() if capture_warnings else nullcontext():
        if capture_warnings:
            warnings.filterwarnings(action="ignore")
        try:
            return _create_model_cached(model_name, **field_definitions)
        except TypeError:
            # something in field definitions is not hashable
            return _create_model_base(
                model_name,
                __config__=_SchemaConfig,
                **_remap_field_definitions(field_definitions),
            )