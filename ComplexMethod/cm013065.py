def _arange_cast_helper(
    g: jit_utils.GraphContext, end, start=None, step=None, dtype=None
) -> tuple[
    _type_utils.JitScalarType,
    _C.Value | None,
    _C.Value | None,
    _C.Value | None,
]:
    def _is_all_integral(scalars):
        for scalar in scalars:
            scalar_type = _type_utils.JitScalarType.from_value(
                scalar, _type_utils.JitScalarType.UNDEFINED
            )
            if (
                scalar_type != _type_utils.JitScalarType.INT64
                and scalar_type != _type_utils.JitScalarType.UNDEFINED
            ):
                return False
        return True

    # This logic is based on torch.arange docs. If "dtype" is provided,
    # infer input types from dtype. If not, then check if any of start, stop,
    # or step are floating point, and infer the type from get_default.
    # Otherwise, the dtype is inferred to be torch.int64.
    if dtype is None or (_is_value(dtype) and _is_none(dtype)):
        if _is_all_integral([start, end, step]):
            scalar_type = _type_utils.JitScalarType.INT64
        else:
            scalar_type = _type_utils.JitScalarType.from_dtype(
                torch.get_default_dtype()
            )
    else:
        if not isinstance(dtype, int):
            raise AssertionError(f"Expected dtype to be int, got {type(dtype)}")
        # TODO(justinchuby): Check if dtype is indeed a int.
        scalar_type = _type_utils.JitScalarType(dtype)

    start = g.op("Cast", start, to_i=scalar_type.onnx_type()) if start else None
    end = g.op("Cast", end, to_i=scalar_type.onnx_type()) if end else None
    step = g.op("Cast", step, to_i=scalar_type.onnx_type()) if step else None
    return scalar_type, end, start, step