def register_dataclass(
    cls: type[Any],
    *,
    field_names: list[str] | None = None,
    drop_field_names: list[str] | None = None,
    serialized_type_name: str | None = None,
) -> None:
    """
    Registers a type that has the semantics of a ``dataclasses.dataclass`` type
    as a pytree node.

    This is a simpler API than :func:`register_pytree_node` for registering
    a dataclass or a custom class with the semantics of a dataclass.

    Args:
        cls: The python type to register. The class must have the semantics of a
        dataclass; in particular, it must be constructed by passing the fields
        in.
        field_names (Optional[List[str]]): A list of field names that correspond
            to the **non-constant data** in this class. This list must contain
            all the fields that are used to initialize the class. This argument
            is optional if ``cls`` is a dataclass, in which case the fields will
            be taken from ``dataclasses.fields()``.
        drop_field_names (Optional[List[str]]): A list of field names that
            should not be included in the pytree.
        serialized_type_name: A keyword argument used to specify the fully
            qualified name used when serializing the tree spec. This is only
            needed for serializing the treespec in torch.export.

    Example:

        >>> from torch import Tensor
        >>> from dataclasses import dataclass
        >>> import torch.utils._pytree as pytree
        >>>
        >>> @dataclass
        >>> class Point:
        >>>     x: Tensor
        >>>     y: Tensor
        >>>
        >>> pytree.register_dataclass(Point)
        >>>
        >>> point = Point(torch.tensor(0), torch.tensor(1))
        >>> point = pytree.tree_map(lambda x: x + 1, point)
        >>> assert torch.allclose(point.x, torch.tensor(1))
        >>> assert torch.allclose(point.y, torch.tensor(2))

    """
    drop_field_names = drop_field_names or []

    if not dataclasses.is_dataclass(cls):
        if field_names is None:
            raise ValueError(
                "field_names must be specified with a list of all fields used to "
                f"initialize {cls}, as it is not a dataclass."
            )
    elif field_names is None:
        field_names = [f.name for f in dataclasses.fields(cls) if f.init]
    else:
        dataclass_init_fields = {f.name for f in dataclasses.fields(cls) if f.init}
        dataclass_init_fields.difference_update(drop_field_names)

        if dataclass_init_fields != set(field_names):
            error_msg = "field_names does not include all dataclass fields.\n"

            if missing := dataclass_init_fields - set(field_names):
                error_msg += (
                    f"Missing fields in `field_names`: {missing}. If you want "
                    "to include these fields in the pytree, please add them "
                    "to `field_names`, otherwise please add them to "
                    "`drop_field_names`.\n"
                )

            if unexpected := set(field_names) - dataclass_init_fields:
                error_msg += (
                    f"Unexpected fields in `field_names`: {unexpected}. "
                    "Please remove these fields, or add them to `drop_field_names`.\n"
                )

            raise ValueError(error_msg)

    def _flatten_fn(obj: Any) -> tuple[list[Any], Context]:
        flattened = []
        flat_names = []
        none_names = []
        for name in field_names:
            val = getattr(obj, name)
            if val is not None:
                flattened.append(val)
                flat_names.append(name)
            else:
                none_names.append(name)
        return flattened, [flat_names, none_names]

    def _unflatten_fn(values: Iterable[Any], context: Context) -> Any:
        flat_names, none_names = context
        return cls(
            **dict(zip(flat_names, values, strict=True)), **dict.fromkeys(none_names)
        )

    def _flatten_fn_with_keys(obj: Any) -> tuple[list[Any], Context]:
        flattened, (flat_names, _none_names) = _flatten_fn(obj)  # type: ignore[misc]
        return [
            (GetAttrKey(k), v) for k, v in zip(flat_names, flattened, strict=True)
        ], flat_names

    _private_register_pytree_node(
        cls,
        _flatten_fn,
        _unflatten_fn,
        serialized_type_name=serialized_type_name,
        flatten_with_keys_fn=_flatten_fn_with_keys,
    )