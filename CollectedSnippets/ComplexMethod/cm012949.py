def get_reversed_fusions() -> list[tuple[NSFusionType, int]]:
    """
    Set of potential fusions, in reverse order.  The order is reversed
    to match how fusion patterns are defined in quantization code.

    Fusion format:
    ((fusion_op_0, fusion_op_1), base_op_idx)

    Where base_op_idx is the idx of the op we should use to match other related
    ops. Note: base_op_idx is specified in non-reverse order, i.e. a base_op_idx
    of 0 represents the first op in regular (non-reverse) order, 1 represents the
    second op, etc.
    """
    results: list[tuple[NSFusionType, int]] = []

    # Possible syntaxes:
    # * single op: torch.nn.Conv2d
    # * multiple ops: (torch.nn.ReLU, torch.nn.Conv2d)
    # For fusions, we only care about patterns composed of multiple ops.
    # TODO(future PR): allow customizations from default patterns.
    all_quant_patterns = _get_pattern_to_quantize_handlers(get_native_backend_config())

    default_base_op_idx = 0
    for quant_pattern in all_quant_patterns:
        # TODO: this is a temporary hack to flatten the patterns from quantization so
        # that it works with the ns matcher function, maybe we should use `_is_match`
        # in torch.ao.quantization.fx.match_utils to match the patterns
        if (
            isinstance(quant_pattern, tuple)
            and len(quant_pattern) == 2
            and isinstance(quant_pattern[1], tuple)
            and len(quant_pattern[1]) == 2
        ):
            # flatten the pattern with form (nn.ReLU, (nn.BatchNorm2d, nn.Conv2d))
            quant_pattern = (quant_pattern[0], quant_pattern[1][0], quant_pattern[1][1])

        # Only patterns of multiple ops are fusions, ignore
        # patterns which contain a single ops (they get matched
        # without caring about fusions).
        if isinstance(quant_pattern, tuple):
            results.append((quant_pattern, default_base_op_idx))  # type: ignore[arg-type]

        # For each pattern, add additional patterns with observers and
        # fake quants at the end.
        # TODO(future PR): if needed, implement matching for a node
        #   having multiple output observers.
        for cls in (ObserverBase, FakeQuantizeBase):
            if isinstance(quant_pattern, tuple):
                # pyrefly: ignore [not-iterable]
                new_pattern = (cls, *quant_pattern)
            else:
                new_pattern = (cls, quant_pattern)
            results.append((new_pattern, default_base_op_idx))  # type: ignore[arg-type]

    # After this point, results contains values such as
    # [..., ((torch.nn.Relu, torch.nn.Conv2d), 0), ...]

    # Patterns for matching fp16 emulation are not specified in the quantization
    # fusion mappings.  For now, define them here.
    fp16_em_base_op_idx = 1
    patterns_to_add = [
        # linear-relu fp16 emulation:
        # fp16_to_fp32 -> linear -> relu -> fp32_to_fp16
        (
            (("to", torch.float16), F.relu, F.linear, "dequantize"),
            fp16_em_base_op_idx,
        ),
        # Conv-BN fusion (this happens outside of quantization patterns,
        # which is why it is defined separately here).
        ((nn.BatchNorm1d, nn.Conv1d), default_base_op_idx),
        ((nn.BatchNorm2d, nn.Conv2d), default_base_op_idx),
        ((nn.BatchNorm3d, nn.Conv3d), default_base_op_idx),
        ((nn.ReLU, nn.BatchNorm1d, nn.Conv1d), default_base_op_idx),
        ((nn.ReLU, nn.BatchNorm2d, nn.Conv2d), default_base_op_idx),
        ((nn.ReLU, nn.BatchNorm3d, nn.Conv3d), default_base_op_idx),
    ]
    for p in patterns_to_add:
        results.append(p)  # type: ignore[arg-type]
        results.append(((ObserverBase, *p[0]), p[1]))  # type: ignore[arg-type]
        results.append(((FakeQuantizeBase, *p[0]), p[1]))  # type: ignore[arg-type]

    return results