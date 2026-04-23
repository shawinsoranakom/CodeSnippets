def get_quant_type(qconfig):
    if qconfig is None:
        raise AssertionError("qconfig must be provided to determine quant type")
    activation = qconfig.activation()
    weight = qconfig.weight()
    static_dtypes = [
        torch.quint8,
        torch.qint8,
        torch.quint4x2,
        torch.qint32,
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.float8_e5m2,
        torch.float8_e4m3fn,
    ]
    if weight.dtype in static_dtypes:
        if hasattr(activation, "is_dynamic") and activation.is_dynamic:
            return QuantType.DYNAMIC
        elif activation.dtype in static_dtypes:
            return QuantType.STATIC
        else:
            return QuantType.WEIGHT_ONLY

    if weight.dtype == torch.float16:
        if hasattr(activation, "is_dynamic") and activation.is_dynamic:
            return QuantType.DYNAMIC
        elif activation.dtype == torch.float16:
            return QuantType.STATIC

    raise Exception(  # noqa: TRY002
        f"Unrecognized dtype combination in get_quant_type: activation({activation.dtype}),"
        f"weight({weight.dtype})"
    )