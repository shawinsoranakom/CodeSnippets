def check_symbols(path, tensor, shape):
        if isinstance(shape, dict):
            for i, dim in shape.items():
                if isinstance(dim, Dim):
                    check_same_bounds(dim)
                elif dim is None:
                    _warn_on_None_dynamic_shape_dimension()
                elif not (isinstance(dim, (int, _DimHint))):
                    raise UserError(
                        UserErrorType.INVALID_INPUT,
                        f"Unexpected dimension mapped to index {i} in input tensor shape {shape} "
                        f"specified at `dynamic_shapes{keystr(path)}` "
                        f"(expected None, an int, a Dim, Dim.AUTO, Dim.STATIC, or Dim.DYNAMIC, "
                        f" but got {dim!r} instead)",
                        case_name="dynamic_shapes_validation",
                    )
        elif isinstance(shape, (tuple, list)):
            if len(shape) != len(tensor.shape):
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Expected dynamic shape spec {shape} specified at `dynamic_shapes{keystr(path)}` "
                    f"to have the same length as the actual tensor shape {tensor.shape} "
                    f"(expected {len(tensor.shape)}, but got {len(shape)} instead)",
                    case_name="dynamic_shapes_validation",
                )
            for i, dim in enumerate(shape):
                if isinstance(dim, Dim):
                    check_same_bounds(dim)
                elif dim is None:
                    _warn_on_None_dynamic_shape_dimension()
                elif not (isinstance(dim, (int, _DimHint))):
                    raise UserError(
                        UserErrorType.INVALID_INPUT,
                        f"Unexpected dimension #{i} in input tensor shape {shape} "
                        f"specified at `dynamic_shapes{keystr(path)}` "
                        f"(expected None, an int, a Dim, Dim.AUTO, Dim.STATIC, or Dim.DYNAMIC, "
                        f"but got {dim!r} instead)",
                        case_name="dynamic_shapes_validation",
                    )
        elif shape is not None:
            raise UserError(
                UserErrorType.INVALID_INPUT,
                f"Unexpected input tensor shape {shape} specified at `dynamic_shapes{keystr(path)}` "
                f"(expected either a list/tuple of dimensions, or a dict mapping indices to dimensions,"
                f" where each dimension is an int, a Dim, Dim.AUTO, Dim.STATIC, or Dim.DYNAMIC)",
                case_name="dynamic_shapes_validation",
            )