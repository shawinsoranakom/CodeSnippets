def _detect_output_quant_key(
    output: torch.Tensor,
    output_scale: torch.Tensor | None,
    output_block_scale: torch.Tensor | None,
    output_dim: int,
) -> QuantKey | None:
    """Detect the output quantization key from fusion pass parameters.

    Returns the appropriate QuantKey, or None if no quantization is needed.
    Detection is based on output dtype and which scale tensors are present.
    """
    if output_scale is None and output_block_scale is None:
        return None
    if output_block_scale is not None:
        if output.dtype == _FP8_DTYPE:
            # Per-group FP8 uses block scales only, not a separate output_scale
            assert output_scale is None
            # Infer group size from scale shape
            num_groups = output_block_scale.shape[-1]
            group_size = output_dim // num_groups
            if group_size == 128:
                return kFp8Dynamic128Sym
            elif group_size == 64:
                return kFp8Dynamic64Sym
            else:
                raise ValueError(
                    f"Unsupported group FP8 group_size={group_size} "
                    f"(output_dim={output_dim}, num_groups={num_groups}). "
                    f"Only group_size 128 and 64 are supported."
                )
        # output_scale None implies MXFP4, not supported
        assert output_scale is not None
        return kNvfp4Dynamic
    return kFp8StaticTensorSym