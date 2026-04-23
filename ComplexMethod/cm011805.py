def unsupported_input_tensor(t: torch.Tensor, node=None):
    "Do not support reading or writing to this tensor"
    if t.is_complex():
        # Complex views are supported with IR ComplexView
        _warn_complex_not_supported()
        return True

    if t.is_meta:
        return True

    if t.is_sparse:
        return True

    if t.dtype == torch.float8_e8m0fnu:
        if not node:
            return True

        # allow bitcast, views, memory movement, but not arithmetic
        # TODO: delete once triton adds native support
        return not (
            isinstance(node.target, torch._ops.OpOverload)
            and node.target
            in (
                aten.view.dtype,
                aten.cat.default,
                aten.clone.default,
                aten._scaled_mm.default,
            )
            or (isinstance(node.target, torch._ops.OpOverload) and is_view(node.target))
        )

    return False