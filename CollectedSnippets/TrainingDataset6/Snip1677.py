def analyze_param(
    *,
    param_name: str,
    annotation: Any,
    value: Any,
    is_path_param: bool,
) -> ParamDetails:
    field_info = None
    depends = None
    type_annotation: Any = Any
    use_annotation: Any = Any
    if is_typealiastype(annotation):
        # unpack in case PEP 695 type syntax is used
        annotation = annotation.__value__
    if annotation is not inspect.Signature.empty:
        use_annotation = annotation
        type_annotation = annotation
    # Extract Annotated info
    if get_origin(use_annotation) is Annotated:
        annotated_args = get_args(annotation)
        type_annotation = annotated_args[0]
        fastapi_annotations = [
            arg
            for arg in annotated_args[1:]
            if isinstance(arg, (FieldInfo, params.Depends))
        ]
        fastapi_specific_annotations = [
            arg
            for arg in fastapi_annotations
            if isinstance(
                arg,
                (
                    params.Param,
                    params.Body,
                    params.Depends,
                ),
            )
        ]
        if fastapi_specific_annotations:
            fastapi_annotation: FieldInfo | params.Depends | None = (
                fastapi_specific_annotations[-1]
            )
        else:
            fastapi_annotation = None
        # Set default for Annotated FieldInfo
        if isinstance(fastapi_annotation, FieldInfo):
            # Copy `field_info` because we mutate `field_info.default` below.
            field_info = copy_field_info(
                field_info=fastapi_annotation,
                annotation=use_annotation,
            )
            assert (
                field_info.default == Undefined or field_info.default == RequiredParam
            ), (
                f"`{field_info.__class__.__name__}` default value cannot be set in"
                f" `Annotated` for {param_name!r}. Set the default value with `=` instead."
            )
            if value is not inspect.Signature.empty:
                assert not is_path_param, "Path parameters cannot have default values"
                field_info.default = value
            else:
                field_info.default = RequiredParam
        # Get Annotated Depends
        elif isinstance(fastapi_annotation, params.Depends):
            depends = fastapi_annotation
    # Get Depends from default value
    if isinstance(value, params.Depends):
        assert depends is None, (
            "Cannot specify `Depends` in `Annotated` and default value"
            f" together for {param_name!r}"
        )
        assert field_info is None, (
            "Cannot specify a FastAPI annotation in `Annotated` and `Depends` as a"
            f" default value together for {param_name!r}"
        )
        depends = value
    # Get FieldInfo from default value
    elif isinstance(value, FieldInfo):
        assert field_info is None, (
            "Cannot specify FastAPI annotations in `Annotated` and default value"
            f" together for {param_name!r}"
        )
        field_info = value
        if isinstance(field_info, FieldInfo):
            field_info.annotation = type_annotation

    # Get Depends from type annotation
    if depends is not None and depends.dependency is None:
        # Copy `depends` before mutating it
        depends = copy(depends)
        depends = dataclasses.replace(depends, dependency=type_annotation)

    # Handle non-param type annotations like Request
    # Only apply special handling when there's no explicit Depends - if there's a Depends,
    # the dependency will be called and its return value used instead of the special injection
    if depends is None and lenient_issubclass(
        type_annotation,
        (
            Request,
            WebSocket,
            HTTPConnection,
            Response,
            StarletteBackgroundTasks,
            SecurityScopes,
        ),
    ):
        assert field_info is None, (
            f"Cannot specify FastAPI annotation for type {type_annotation!r}"
        )
    # Handle default assignations, neither field_info nor depends was not found in Annotated nor default value
    elif field_info is None and depends is None:
        default_value = value if value is not inspect.Signature.empty else RequiredParam
        if is_path_param:
            # We might check here that `default_value is RequiredParam`, but the fact is that the same
            # parameter might sometimes be a path parameter and sometimes not. See
            # `tests/test_infer_param_optionality.py` for an example.
            field_info = params.Path(annotation=use_annotation)
        elif is_uploadfile_or_nonable_uploadfile_annotation(
            type_annotation
        ) or is_uploadfile_sequence_annotation(type_annotation):
            field_info = params.File(annotation=use_annotation, default=default_value)
        elif not field_annotation_is_scalar(annotation=type_annotation):
            field_info = params.Body(annotation=use_annotation, default=default_value)
        else:
            field_info = params.Query(annotation=use_annotation, default=default_value)

    field = None
    # It's a field_info, not a dependency
    if field_info is not None:
        # Handle field_info.in_
        if is_path_param:
            assert isinstance(field_info, params.Path), (
                f"Cannot use `{field_info.__class__.__name__}` for path param"
                f" {param_name!r}"
            )
        elif (
            isinstance(field_info, params.Param)
            and getattr(field_info, "in_", None) is None
        ):
            field_info.in_ = params.ParamTypes.query
        use_annotation_from_field_info = use_annotation
        if isinstance(field_info, params.Form):
            ensure_multipart_is_installed()
        if not field_info.alias and getattr(field_info, "convert_underscores", None):
            alias = param_name.replace("_", "-")
        else:
            alias = field_info.alias or param_name
        field_info.alias = alias
        field = create_model_field(
            name=param_name,
            type_=use_annotation_from_field_info,
            default=field_info.default,
            alias=alias,
            field_info=field_info,
        )
        if is_path_param:
            assert is_scalar_field(field=field), (
                "Path params must be of one of the supported types"
            )
        elif isinstance(field_info, params.Query):
            assert (
                is_scalar_field(field)
                or field_annotation_is_scalar_sequence(field.field_info.annotation)
                or lenient_issubclass(field.field_info.annotation, BaseModel)
            ), f"Query parameter {param_name!r} must be one of the supported types"

    return ParamDetails(type_annotation=type_annotation, depends=depends, field=field)