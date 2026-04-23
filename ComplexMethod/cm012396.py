def _has_unsupported_captured_scalars(
    score_mod_other_buffers: Sequence[Any],
    mask_mod_other_buffers: Sequence[Any],
) -> bool:
    """Check if any captured buffers are dynamic scalars that cannot be inlined.

    When compiling with dynamic=True, captured Python scalars in score_mod or
    mask_mod may become:
    - sympy symbols from LocalSource (captured ints) - NOT from tensor shapes
    - 0-dim CPU tensors (captured floats)

    Symbols from TensorPropertySource (tensor size/stride) are fine because they
    get resolved at runtime.

    The FLASH backend cannot inline captured scalar symbolic values into the CuteDSL template.
    """
    from torch._inductor.virtualized import V

    shape_env = V.graph.sizevars.shape_env

    for buf in list(score_mod_other_buffers) + list(mask_mod_other_buffers):
        # Captured int becomes sympy.Symbol - check if it's NOT from a tensor shape
        if isinstance(buf, sympy.Expr):
            for symbol in buf.free_symbols:
                if not _is_symbol_from_tensor_shape(symbol, shape_env):
                    return True
        # Captured float becomes 0-dim TensorBox on CPU
        if isinstance(buf, TensorBox):
            device = buf.get_device()
            size = buf.get_size()
            if device is not None and device.type == "cpu" and len(size) == 0:
                # 0-dimensional CPU tensor (scalar) - can't be inlined into CUDA kernel
                return True
    return False