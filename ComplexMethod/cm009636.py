def _convert_any_typed_dicts_to_pydantic(
    type_: type,
    *,
    visited: dict[type, type],
    depth: int = 0,
) -> type:
    if type_ in visited:
        return visited[type_]
    if depth >= _MAX_TYPED_DICT_RECURSION:
        return type_
    if is_typeddict(type_):
        typed_dict = type_
        docstring = inspect.getdoc(typed_dict)
        # Use get_type_hints to properly resolve forward references and
        # string annotations in Python 3.14+ (PEP 649 deferred annotations).
        # include_extras=True preserves Annotated metadata.
        try:
            annotations_ = get_type_hints(typed_dict, include_extras=True)
        except Exception:
            # Fallback for edge cases where get_type_hints might fail
            annotations_ = typed_dict.__annotations__
        description, arg_descriptions = _parse_google_docstring(
            docstring, list(annotations_)
        )
        fields: dict = {}
        for arg, arg_type in annotations_.items():
            if get_origin(arg_type) in {Annotated, typing_extensions.Annotated}:
                annotated_args = get_args(arg_type)
                new_arg_type = _convert_any_typed_dicts_to_pydantic(
                    annotated_args[0], depth=depth + 1, visited=visited
                )
                field_kwargs = dict(
                    zip(("default", "description"), annotated_args[1:], strict=False)
                )
                if (field_desc := field_kwargs.get("description")) and not isinstance(
                    field_desc, str
                ):
                    msg = (
                        f"Invalid annotation for field {arg}. Third argument to "
                        f"Annotated must be a string description, received value of "
                        f"type {type(field_desc)}."
                    )
                    raise ValueError(msg)
                if arg_desc := arg_descriptions.get(arg):
                    field_kwargs["description"] = arg_desc
                fields[arg] = (new_arg_type, Field_v1(**field_kwargs))
            else:
                new_arg_type = _convert_any_typed_dicts_to_pydantic(
                    arg_type, depth=depth + 1, visited=visited
                )
                field_kwargs = {"default": ...}
                if arg_desc := arg_descriptions.get(arg):
                    field_kwargs["description"] = arg_desc
                fields[arg] = (new_arg_type, Field_v1(**field_kwargs))
        model = cast(
            "type[BaseModelV1]", create_model_v1(typed_dict.__name__, **fields)
        )
        model.__doc__ = description
        visited[typed_dict] = model
        return model
    if (origin := get_origin(type_)) and (type_args := get_args(type_)):
        subscriptable_origin = _py_38_safe_origin(origin)
        type_args = tuple(
            _convert_any_typed_dicts_to_pydantic(arg, depth=depth + 1, visited=visited)
            for arg in type_args
        )
        return cast("type", subscriptable_origin[type_args])  # type: ignore[index]
    return type_