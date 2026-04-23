def _get_allowed_types_from_type_annotation(
    type_: TypeAnnotationValue,
) -> set[ir.TypeProtocol]:
    """Obtain the allowed types from a type annotation."""
    if type_ is onnxscript.onnx_types.TensorType:
        # Any tensor type
        return {ir.TensorType(dtype) for dtype in ir.DataType}

    allowed_types: set[ir.TypeProtocol]

    if isinstance(type_, TypeVar):
        allowed_types = set()
        if constraints := type_.__constraints__:
            for constraint in constraints:
                allowed_types.update(
                    _get_allowed_types_from_type_annotation(constraint)
                )
        else:
            bound = type_.__bound__
            if bound is None:
                allowed_types = _ALL_VALUE_TYPES  # type: ignore[assignment]
            else:
                allowed_types.update(_get_allowed_types_from_type_annotation(bound))
        return allowed_types
    if hasattr(type_, "dtype"):
        # A single tensor type like INT64, FLOAT, etc.
        return {ir.TensorType(ir.DataType(type_.dtype))}
    if _is_optional(type_):
        allowed_types = set()
        subtypes = typing.get_args(type_)
        for subtype in subtypes:
            if subtype is type(None):
                continue
            allowed_types.update(_get_allowed_types_from_type_annotation(subtype))
        # NOTE: We do not consider dynamic optional types like optional(float) because they are not very useful.
        return allowed_types

    origin_type = typing.get_origin(type_)
    if origin_type is Union:
        allowed_types = set()
        subtypes = typing.get_args(type_)
        for subtype in subtypes:
            if subtype is type(None):
                raise AssertionError(
                    "Union should not contain None type because it is handled by _is_optional."
                )
            allowed_types.update(_get_allowed_types_from_type_annotation(subtype))
        return allowed_types

    if isinstance(origin_type, type) and issubclass(origin_type, Sequence):
        subtypes = typing.get_args(type_)
        return {
            ir.SequenceType(t)
            for t in _get_allowed_types_from_type_annotation(subtypes[0])
        }

    # Allow everything by default
    return _ALL_VALUE_TYPES