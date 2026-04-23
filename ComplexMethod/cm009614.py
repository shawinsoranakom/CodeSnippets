def get_all_basemodel_annotations(
    cls: TypeBaseModel | Any, *, default_to_bound: bool = True
) -> dict[str, type | TypeVar]:
    """Get all annotations from a Pydantic `BaseModel` and its parents.

    Args:
        cls: The Pydantic `BaseModel` class.
        default_to_bound: Whether to default to the bound of a `TypeVar` if it exists.

    Returns:
        `dict` of field names to their type annotations.
    """
    # cls has no subscript: cls = FooBar
    if isinstance(cls, type):
        fields = get_fields(cls)
        alias_map = {field.alias: name for name, field in fields.items() if field.alias}

        annotations: dict[str, type | TypeVar] = {}
        for name, param in inspect.signature(cls).parameters.items():
            # Exclude hidden init args added by pydantic Config. For example if
            # BaseModel(extra="allow") then "extra_data" will part of init sig.
            if name not in fields and name not in alias_map:
                continue
            field_name = alias_map.get(name, name)
            annotations[field_name] = param.annotation
        orig_bases: tuple = getattr(cls, "__orig_bases__", ())
    # cls has subscript: cls = FooBar[int]
    else:
        annotations = get_all_basemodel_annotations(
            get_origin(cls), default_to_bound=False
        )
        orig_bases = (cls,)

    # Pydantic v2 automatically resolves inherited generics, Pydantic v1 does not.
    if not (isinstance(cls, type) and is_pydantic_v2_subclass(cls)):
        # if cls = FooBar inherits from Baz[str], orig_bases will contain Baz[str]
        # if cls = FooBar inherits from Baz, orig_bases will contain Baz
        # if cls = FooBar[int], orig_bases will contain FooBar[int]
        for parent in orig_bases:
            # if class = FooBar inherits from Baz, parent = Baz
            if isinstance(parent, type) and is_pydantic_v1_subclass(parent):
                annotations.update(
                    get_all_basemodel_annotations(parent, default_to_bound=False)
                )
                continue

            parent_origin = get_origin(parent)

            # if class = FooBar inherits from non-pydantic class
            if not parent_origin:
                continue

            # if class = FooBar inherits from Baz[str]:
            # parent = class Baz[str],
            # parent_origin = class Baz,
            # generic_type_vars = (type vars in Baz)
            # generic_map = {type var in Baz: str}
            generic_type_vars: tuple = getattr(parent_origin, "__parameters__", ())
            generic_map = dict(zip(generic_type_vars, get_args(parent), strict=False))
            for field in getattr(parent_origin, "__annotations__", {}):
                annotations[field] = _replace_type_vars(
                    annotations[field], generic_map, default_to_bound=default_to_bound
                )

    return {
        k: _replace_type_vars(v, default_to_bound=default_to_bound)
        for k, v in annotations.items()
    }