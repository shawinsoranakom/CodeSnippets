def native_layer_norm(
    g: jit_utils.GraphContext,
    input: _C.Value,
    normalized_shape: Sequence[int],
    weight: _C.Value,
    bias: _C.Value,
    eps: float,
) -> tuple[_C.Value, _C.Value, _C.Value]:
    axes = [-i for i in range(len(normalized_shape), 0, -1)]

    two_cst = symbolic_helper._generate_wrapped_number(g, 2.0)
    eps_cst = symbolic_helper._generate_wrapped_number(g, eps)

    if g.opset < 18:
        mean = g.op("ReduceMean", input, axes_i=axes)
    else:
        mean = g.op(
            "ReduceMean",
            input,
            g.op("Constant", value_t=torch.tensor(axes, dtype=torch.long)),
        )

    numerator = sub(g, input, mean)

    # Cast it to eps dtype to avoid precision loss
    is_type_half = (
        _type_utils.JitScalarType.from_value(numerator)
        == _type_utils.JitScalarType.HALF
    )
    if is_type_half:
        eps_dtype = _type_utils.JitScalarType.from_value(eps_cst)
        numerator = g.op(
            "Cast", numerator, to_i=_type_utils.JitScalarType(eps_dtype).onnx_type()
        )

    # variance = e((x - e(x))^2), and (x - e(x)) is the numerator in the layer_norm formula
    if g.opset < 18:
        # pyrefly: ignore [no-matching-overload]
        variance = g.op("ReduceMean", pow(g, numerator, two_cst), axes_i=axes)
    else:
        variance = g.op(
            "ReduceMean",
            # pyrefly: ignore [no-matching-overload]
            pow(g, numerator, two_cst),
            g.op("Constant", value_t=torch.tensor(axes, dtype=torch.long)),
        )

    denominator = sqrt(g, g.op("Add", variance, eps_cst))
    normalized = g.op("Div", numerator, denominator)

    # Cast back to input type as eps related ops are all done
    if is_type_half:
        input_dtype = _type_utils.JitScalarType.from_value(input)
        normalized = g.op(
            "Cast", normalized, to_i=_type_utils.JitScalarType(input_dtype).onnx_type()
        )

    if not (weight is None or symbolic_helper._is_none(weight)):
        normalized = mul(g, normalized, weight)
    if not (bias is None or symbolic_helper._is_none(bias)):
        normalized = add(g, normalized, bias)

    # rdenominator := 1 / sqrt(variance + eps)
    # According to aten::native_layer_norm, rdenominator should have the same dtype as input,
    # mean and normalized, so we need to Cast it back
    if is_type_half:
        denominator = g.op(
            "Cast",
            denominator,
            to_i=_type_utils.JitScalarType(input_dtype).onnx_type(),  # type: ignore[possibly-undefined]
        )
        rdenominator = g.op("Reciprocal", denominator)
    else:
        rdenominator = reciprocal(g, denominator)

    return normalized, mean, rdenominator