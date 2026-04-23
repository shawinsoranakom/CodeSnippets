def bernoulli(g: jit_utils.GraphContext, input, p=None, generator=None, out=None):
    if out is not None and not symbolic_helper._is_none(out):
        symbolic_helper._unimplemented(
            "Bernoulli", "out parameter is not supported for bernoulli", input
        )
    if generator is not None and not symbolic_helper._is_none(generator):
        symbolic_helper._unimplemented(
            "Bernoulli", "generator is not supported for bernoulli", input
        )

    dtype = _type_utils.JitScalarType.from_value(
        input, _type_utils.JitScalarType.UNDEFINED
    )
    if dtype == _type_utils.JitScalarType.UNDEFINED:
        return symbolic_helper._unimplemented(
            "Bernoulli", "input dtype not accessible", input
        )

    rands = g.op(
        "RandomUniformLike",
        input,
        high_f=1.0,
        low_f=0.0,
        dtype_i=dtype.onnx_type(),
    )
    prob = p if p is not None and not symbolic_helper._is_none(p) else input
    output = g.op("Less", rands, prob)
    return g.op("Cast", output, to_i=dtype.onnx_type())