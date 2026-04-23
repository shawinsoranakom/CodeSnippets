def calculate_qmin_qmax(
    quant_min: int,
    quant_max: int,
    has_customized_qrange: bool,
    dtype: torch.dtype,
    reduce_range: bool,
) -> tuple[int, int]:
    r"""Calculates actual qmin and qmax based on the quantization range,
    observer datatype and if range is reduced.
    """
    # TODO(jerryzh): Figure out why custom quant_min/quant_max are still adjusted.
    if has_customized_qrange:
        # This initialization here is to be resolve TorchScript compilation issues and allow
        # using of refinement to decouple initial_qmin and initial_qmax from quantization range.
        # The actual values of initial_qmin and initial_qmax will be reset below.
        if dtype in [torch.qint32, torch.int32]:
            initial_quant_min, initial_quant_max = 0, 2**32 - 1
        else:
            initial_quant_min, initial_quant_max = 0, 255
        # The following assignment of self.qmin and self.qmax to the local variables and the if check refine the
        # attribute from Optional valid integers for use, based on TorchScript's requirements.
        custom_quant_min, custom_quant_max = quant_min, quant_max
        if custom_quant_min is not None and custom_quant_max is not None:
            initial_quant_min, initial_quant_max = (
                custom_quant_min,
                custom_quant_max,
            )

        qrange_len = initial_quant_max - initial_quant_min + 1
        if dtype in [torch.qint8, torch.int8]:
            if not (0 < qrange_len <= 256):
                raise AssertionError(
                    "quantization range should be positive and not exceed the maximum bit range (=256)."
                )
        elif dtype in [torch.qint32, torch.int32]:
            if not (0 < qrange_len <= 2**32):
                raise AssertionError(
                    "quantization range should be positive and not exceed the maximum bit range (=4294967296)."
                )
        if reduce_range:
            quant_min, quant_max = quant_min // 2, quant_max // 2
    else:
        # Fallback onto default 8-bit qmin and qmax calculation if dynamic range is not used.
        if dtype in [torch.qint8, torch.int8]:
            if reduce_range:
                quant_min, quant_max = -64, 63
            else:
                quant_min, quant_max = -128, 127
        elif dtype in [torch.quint8, torch.uint8]:
            if reduce_range:
                quant_min, quant_max = 0, 127
            else:
                quant_min, quant_max = 0, 255
        elif dtype in [torch.qint32, torch.int32]:
            quant_min, quant_max = -1 * (2**31), (2**31) - 1
        elif dtype == torch.uint16:
            quant_min, quant_max = 0, 2**16 - 1
        elif dtype == torch.int16:
            quant_min, quant_max = -(2**15), 2**15 - 1
        else:
            quant_min, quant_max = 0, 15
    return quant_min, quant_max