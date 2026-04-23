def _load_dynamic_shapes(
    spec: DynamicShapesSpec | dict[str, Any],
    from_dict: bool | None = False,
) -> dict[str, Any] | tuple[Any] | list[Any] | None:
    """
    Utility function for dynamic shapes serialization.
    Deserializes a DynamicShapesSpec or corresponding dictionary into a dynamic_shapes input to export().
    """
    import sympy

    from torch.fx.experimental.symbolic_shapes import _is_supported_equivalence

    if from_dict:
        if not isinstance(spec, dict):
            raise UserError(
                UserErrorType.INVALID_INPUT,
                f"With from_dict=True, expected `spec` to be a dict, got {type(spec)}",
            )
        if sorted(spec.keys()) != ["dims", "dynamic_shapes"]:
            raise UserError(
                UserErrorType.INVALID_INPUT,
                "With from_dict=True, expected `spec` to have keys `dims` and `dynamic_shapes`, "
                f"instead found {spec.keys()}",
            )
        dims = {}
        for k, v in spec["dims"].items():
            if not isinstance(k, str):
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Expected `spec['dims']` keys to be strings for symbols, got key {type(k)}",
                )
            if sorted(v.keys()) != ["derived", "max", "min"]:
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Expected `spec['dims']` values to have keys `derived`, `max`, and `min`, "
                    f"instead found {v.keys()}",
                )
            if not isinstance(v["min"], int):
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Expected dims in `spec['dims']` to map `min` to an int, got {k}: {v['min']}",
                )
            if not isinstance(v["max"], int) or v["max"] is None:
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Expected dims in `spec['dims']` to map `max` to an int or None, got {k}: {v['max']}",
                )
            if not isinstance(v["derived"], list) or any(
                not isinstance(d, str) for d in v["derived"]
            ):
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    "Expected dims in `spec['dims']` to map `derived` to a list of derived expressions, "
                    f"got {k}: {v['derived']}",
                )
            dims[k] = RootDim(**v)
        dynamic_shapes = spec["dynamic_shapes"]
    else:
        if not isinstance(spec, DynamicShapesSpec):
            raise UserError(
                UserErrorType.INVALID_INPUT,
                f"Expected `spec` to be a DynamicShapesSpec, got {type(spec)}",
            )
        dims = spec.dims
        dynamic_shapes = spec.dynamic_shapes

    if dynamic_shapes is None:
        return None

    dim_cache = {}
    for name, info in dims.items():
        symbol = sympy.sympify(name)
        if not isinstance(symbol, sympy.Symbol):
            raise UserError(
                UserErrorType.INVALID_INPUT,
                f"Expected `spec['dims']` keys to be symbols, got {name}",
            )
        dim_cache[name] = Dim(name, min=info.min, max=info.max)  # cache root dim
        for _expr in info.derived:
            expr = sympy.sympify(_expr)
            if len(expr.free_symbols) != 1 or symbol not in expr.free_symbols:
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Expected derived expressions in to have {name} as the only free symbol, got {expr}",
                )
            if not _is_supported_equivalence(expr):
                raise UserError(
                    UserErrorType.INVALID_INPUT,
                    f"Expected derived expressions to be linear expressions, got {expr}",
                )
            modulus, remainder = sympy.polys.polytools.div(expr, symbol)
            ddim = dim_cache[name]
            if modulus != 1:
                ddim = int(modulus) * ddim  # type: ignore[assignment, operator]
            if remainder != 0:
                ddim = ddim + int(remainder)  # type: ignore[assignment, operator]
            dim_cache[_expr] = ddim  # cache derived dims

    def deserialize_shape(
        val: None | int | str,
    ) -> None | int | Dim | _DimHint:
        if val is None or isinstance(val, int):
            return val
        elif val == "_DimHint.AUTO":
            return _DimHint.AUTO()
        elif val == "_DimHint.DYNAMIC":
            return _DimHint.DYNAMIC()
        elif val == "_DimHint.STATIC":
            return _DimHint.STATIC()
        if not isinstance(val, str):
            raise UserError(
                UserErrorType.INVALID_INPUT,
                "Expected leaves in `spec['dynamic_shapes']` to be ints, None, Dim.AUTO/STATIC, symbols, "
                f" or derived expressions, got {val}",
            )
        if val not in dim_cache:
            raise UserError(
                UserErrorType.INVALID_INPUT,
                "Expected dims in `spec['dynamic_shapes']` to be tracked in `spec['dims']`, "
                f"got {val} which is not in {dims.keys()}",
            )
        return dim_cache[val]  # type: ignore[return-value]

    return tree_map(deserialize_shape, dynamic_shapes)