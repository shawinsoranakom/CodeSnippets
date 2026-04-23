def _compare_onnx_pytorch_outputs_in_np(
    onnx_outs: _OutputsType,
    pt_outs: _OutputsType,
    options: VerificationOptions,
) -> None:
    if len(onnx_outs) != len(pt_outs):
        raise AssertionError(
            f"Number of outputs differ ONNX runtime: ({len(onnx_outs)}) PyTorch: ({len(pt_outs)})"
        )
    acceptable_error_percentage = options.acceptable_error_percentage
    if acceptable_error_percentage and (
        acceptable_error_percentage > 1.0 or acceptable_error_percentage < 0.0
    ):
        raise ValueError(
            "If set, acceptable_error_percentage should be between 0.0 and 1.0"
        )

    for ort_out, pt_out in zip(onnx_outs, pt_outs):
        try:
            # TODO: Remove `check_shape` option once every shape inconsistent issue is addressed.
            if not options.check_shape:
                # Allow different but broadcastable output shapes.
                ort_out, pt_out = np.broadcast_arrays(ort_out, pt_out)
            torch.testing.assert_close(
                ort_out,
                pt_out,
                rtol=options.rtol,
                atol=options.atol,
                check_dtype=options.check_dtype,
                equal_nan=True,
            )
        except AssertionError as e:
            if acceptable_error_percentage:
                error_percentage = 1 - np.sum(
                    np.isclose(ort_out, pt_out, rtol=options.rtol, atol=options.atol)
                ) / np.prod(ort_out.shape)  # pyrefly: ignore [missing-attribute]
                if error_percentage <= acceptable_error_percentage:
                    warnings.warn(
                        f"Suppressed AssertionError:\n{e}.\n"
                        f"Error percentage {error_percentage} "
                        f"within acceptable range {acceptable_error_percentage}.",
                        stacklevel=2,
                    )
                    continue
            # pyrefly: ignore [missing-attribute]
            if ort_out.dtype == np.uint8 or ort_out.dtype == np.int8:
                warnings.warn("ONNX output is quantized", stacklevel=2)
            # pyrefly: ignore [missing-attribute]
            if pt_out.dtype == np.uint8 or pt_out.dtype == np.int8:
                warnings.warn("PyTorch output is quantized", stacklevel=2)
            raise