def format_params(
        path: str,
        parameter_map: dict[str, Parameter],
        func: Callable | None = None,
    ) -> OrderedDict[str, Parameter]:
        """Format the params."""
        # Parse docstring descriptions as fallback for unannotated params
        docstring_descs = MethodDefinition._parse_docstring_params(func)

        parameter_map.pop("cc", None)

        # Extract path parameters from the route path
        path_params = PathHandler.extract_path_parameters(path)

        # we need to add the chart parameter here bc of the docstring generation
        if CHARTING_INSTALLED and path.replace("/", "_")[1:] in Charting.functions():
            parameter_map["chart"] = Parameter(
                name="chart",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Annotated[
                    bool,
                    Query(
                        description="Whether to create a chart or not, by default False.",
                    ),
                ],
                default=False,
            )

        formatted: dict[str, Parameter] = {}
        var_kw = []

        # First, handle path parameters - they must come first
        for name in path_params:
            if name in parameter_map:
                formatted[name] = Parameter(
                    name=name,
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=Annotated[
                        str,
                        OpenBBField(
                            description=f"Path parameter: {name}",
                        ),
                    ],
                    default=Parameter.empty,  # Path params are always required
                )

        # Then process all other parameters
        for name, param in parameter_map.items():
            # Skip path parameters - they should be required string parameters
            if name in path_params or name in ("kwargs", "**kwargs"):
                continue  # Already handled above

            # Case 1: Handle Query objects inside Annotated
            if isinstance(param.annotation, _AnnotatedAlias):
                has_depends = any(
                    hasattr(meta, "dependency")
                    for meta in param.annotation.__metadata__
                )
                model = param.annotation.__args__[0]
                is_pydantic_model = hasattr(type(model), "model_fields") or hasattr(
                    model, "__pydantic_fields__"
                )
                is_get_request = not MethodDefinition.is_data_processing_function(path)

                if is_pydantic_model and is_get_request and not has_depends:
                    # Unpack the model fields as query parameters
                    fields = getattr(
                        type(model),
                        "model_fields",
                        getattr(model, "__pydantic_fields__", {}),
                    )
                    for field_name, field in fields.items():
                        type_ = field.annotation
                        default = (
                            field.default
                            if field.default is not PydanticUndefined
                            else Parameter.empty
                        )
                        description = getattr(field, "description", "")

                        extra = getattr(field, "json_schema_extra", {}) or {}
                        new_type = MethodDefinition.get_expanded_type(
                            field_name, extra, type_
                        )
                        updated_type = (
                            type_ if new_type is ... else Union[type_, new_type]  # noqa
                        )

                        formatted[field_name] = Parameter(
                            name=field_name,
                            kind=Parameter.POSITIONAL_OR_KEYWORD,
                            annotation=Annotated[
                                updated_type,
                                OpenBBField(
                                    description=description,
                                ),
                            ],
                            default=default,
                        )
                    continue

                query_obj = None
                # Look for Query object in the metadata
                for meta in param.annotation.__metadata__:
                    if (
                        hasattr(meta, "__class__")
                        and "Query" in meta.__class__.__name__
                    ):
                        query_obj = meta
                        break
                if query_obj:
                    description = getattr(query_obj, "description", "") or ""
                    default_value = getattr(query_obj, "default", Parameter.empty)
                    if default_value is PydanticUndefined:
                        default_value = Parameter.empty

                    # Create a new annotation with OpenBBField containing the description
                    formatted[name] = Parameter(
                        name=name,
                        kind=param.kind,
                        annotation=Annotated[
                            param.annotation.__args__[0],  # Get the original type
                            OpenBBField(
                                description=description,
                            ),
                        ],
                        default=param.default,
                    )
                    continue

            # Case 2: Handle Query objects as default values
            if (
                hasattr(param.default, "__class__")
                and "Query" in param.default.__class__.__name__
            ):
                query_obj = param.default
                description = getattr(query_obj, "description", "") or ""
                default_value = getattr(query_obj, "default", "")
                formatted[name] = Parameter(
                    name=name,
                    kind=param.kind,
                    annotation=Annotated[
                        param.annotation,
                        OpenBBField(
                            description=description,
                        ),
                    ],
                    default=(
                        Parameter.empty
                        if default_value is PydanticUndefined
                        or default_value is Ellipsis
                        else default_value
                    ),
                )
                continue

            if name == "extra_params":
                formatted[name] = Parameter(name="kwargs", kind=Parameter.VAR_KEYWORD)
                var_kw.append(name)
            elif name == "provider_choices":
                if param.annotation != Parameter.empty and hasattr(
                    param.annotation, "__args__"
                ):
                    fields = param.annotation.__args__[0].__dataclass_fields__
                    field = fields["provider"]
                else:
                    continue
                type_ = getattr(field, "type")
                default_priority = getattr(type_, "__args__")
                formatted["provider"] = Parameter(
                    name="provider",
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=Annotated[
                        Optional[MethodDefinition.get_type(field)],  # noqa
                        OpenBBField(
                            description=(
                                "The provider to use, by default None. "
                                "If None, the priority list configured in the settings is used. "
                                f"Default priority: {', '.join(default_priority)}."
                            ),
                        ),
                    ],
                    default=None,
                )

            elif MethodDefinition.is_annotated_dc(param.annotation):
                fields = param.annotation.__args__[0].__dataclass_fields__
                for field_name, field in fields.items():
                    type_ = MethodDefinition.get_type(field)
                    default = MethodDefinition.get_default(field)
                    extra = MethodDefinition.get_extra(field)
                    new_type = MethodDefinition.get_expanded_type(
                        field_name, extra, type_
                    )
                    updated_type = (
                        type_ if new_type is ... else Union[type_, new_type]  # noqa
                    )

                    formatted[field_name] = Parameter(
                        name=field_name,
                        kind=Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=updated_type,
                        default=default,
                    )

            if isinstance(param.annotation, _AnnotatedAlias):
                # Specifically look for Depends dependency rather than any annotation
                has_depends = any(
                    hasattr(meta, "dependency")
                    for meta in param.annotation.__metadata__
                )
                if has_depends:
                    continue

                # If not a dependency, process it as a normal parameter
                new_type = MethodDefinition.get_expanded_type(name)
                updated_type = (
                    param.annotation
                    if new_type is ...
                    else Union[param.annotation, new_type]  # noqa
                )

                metadata = getattr(param.annotation, "__metadata__", [])
                description = (
                    getattr(metadata[0], "description", "") if metadata else ""
                )
                # Fall back to docstring description if annotation has none
                if not description:
                    description = docstring_descs.get(name, "")

                formatted[name] = Parameter(
                    name=name,
                    kind=param.kind,
                    annotation=Annotated[
                        updated_type,
                        OpenBBField(
                            description=description,
                        ),
                    ],
                    default=MethodDefinition.get_default(param),  # type: ignore
                )

            else:
                new_type = MethodDefinition.get_expanded_type(name)
                if hasattr(new_type, "__constraints__"):
                    types = new_type.__constraints__ + (param.annotation,)  # type: ignore
                    updated_type = Union[types]  # type: ignore  # noqa
                else:
                    updated_type = (
                        param.annotation
                        if new_type is ...
                        else Union[param.annotation, new_type]  # noqa
                    )

                metadata = getattr(param.annotation, "__metadata__", [])
                description = (
                    getattr(metadata[0], "description", "") if metadata else ""
                )
                # Fall back to docstring description if annotation has none
                if not description:
                    description = docstring_descs.get(name, "")

                # Untyped positional arguments are typed as Any
                updated_type = (
                    Any
                    if updated_type is inspect._empty  # pylint: disable=W0212
                    else updated_type
                )

                formatted[name] = Parameter(
                    name=name,
                    kind=param.kind,
                    annotation=Annotated[
                        updated_type,
                        OpenBBField(
                            description=description,
                        ),
                    ],
                    default=MethodDefinition.get_default(param),  # type: ignore
                )
                if param.kind == Parameter.VAR_KEYWORD:
                    var_kw.append(name)

        required_params = OrderedDict()
        optional_params = OrderedDict()

        for name, param in formatted.items():
            if param.default == Parameter.empty:
                required_params[name] = param
            else:
                optional_params[name] = param

        # Combine them in the correct order
        ordered_params = OrderedDict(
            list(required_params.items()) + list(optional_params.items())
        )

        return MethodDefinition.reorder_params(params=ordered_params, var_kw=var_kw)