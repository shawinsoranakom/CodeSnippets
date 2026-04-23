def _check_dynamic_shapes(
    combined_args: dict[str, Any],
    dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any] | None,
):
    """
    Checks the dynamic_shapes specification for correctness,
    using combined args + kwargs as reference for inputs structure.
    """
    from torch._dynamo.exc import UserError, UserErrorType

    if dynamic_shapes is None or len(dynamic_shapes) == 0:
        return
    if isinstance(dynamic_shapes, (tuple, list)):
        combined_args = type(dynamic_shapes)(combined_args.values())  # type: ignore[assignment, misc]

    bounds: dict[str, tuple[int, int]] = {}

    def check_same_bounds(dim):
        if dim.__name__ in bounds:
            min_, max_ = bounds[dim.__name__]
            if dim.min != min_ or dim.max != max_:
                this_ = Dim._readable(dim.__name__, min_, max_)
                that_ = Dim._readable(dim.__name__, dim.min, dim.max)
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Found different definitions {this_} and {that_} "
                    f"for the same symbolic dimension {dim}!",
                )
        else:
            bounds[dim.__name__] = (dim.min, dim.max)

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

    if not isinstance(dynamic_shapes, (dict, tuple, list)):
        raise AssertionError(
            f"expected dynamic_shapes to be dict, tuple, or list, got {type(dynamic_shapes)}"
        )
    if isinstance(dynamic_shapes, dict):
        got_keys = list(dynamic_shapes.keys())
        expected_arg_names = list(combined_args.keys())
        if sorted(got_keys) != sorted(expected_arg_names):
            msg = (
                f"When `dynamic_shapes` is specified as a dict, its top-level keys "
                f"must be the arg names {expected_arg_names} of `inputs`, but "
                f"here they are {got_keys}. "
            )
            if (
                len(combined_args) == 1
                and expected_arg_names[0] not in got_keys
                and isinstance(combined_args[expected_arg_names[0]], dict)
            ):
                msg += (
                    "Since here `inputs` is a list/tuple enclosing a single dict, "
                    "maybe you just forgot to enclose `dynamic_shapes` in a list/tuple?"
                )
            else:
                msg += (
                    "Alternatively, you could also ignore arg names entirely "
                    "and specify `dynamic_shapes` as a list/tuple matching `inputs`."
                )
            raise UserError(
                UserErrorType.INVALID_INPUT, msg, case_name="dynamic_shapes_validation"
            )

    def check_shape(path, t, dynamic_shape):
        if isinstance(t, torch.Tensor):
            check_symbols(path, t, dynamic_shape)
        elif isinstance(t, _IntWrapper):
            if isinstance(dynamic_shape, _Dim):
                raise ValueError(
                    "Unable to specify input integers as dynamic through named "
                    "Dims. Please use Dim.AUTO/DYNAMIC instead."
                )
            if dynamic_shape is not None and not isinstance(
                dynamic_shape, (int, _DimHint)
            ):
                raise AssertionError(
                    f"expected dynamic_shape to be None, int, or _DimHint for _IntWrapper, got {type(dynamic_shape)}"
                )
        else:
            if dynamic_shape is not None:
                rendered_path = keystr(path)
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Cannot associate shape {dynamic_shape} specified at `dynamic_shapes{rendered_path}` "
                    f"to non-tensor type {type(t)} at `inputs{rendered_path}` (expected None)",
                    case_name="dynamic_shapes_validation",
                )

    _tree_map_with_path(check_shape, combined_args, dynamic_shapes, tree_name="inputs")