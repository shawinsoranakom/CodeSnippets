def is_mkldnn_conv(node: Node) -> bool:
    # When mkldnn_fusion is enabled, conv will be replaced by the lowering pattern function.
    # See _register_unary_fusion_lowering in torch/_inductor/fx_passes/mkldnn_fusion.py.
    if (
        getattr(torch.ops, "mkldnn", None) is not None
        and getattr(torch.ops.mkldnn, "_convolution_pointwise", None) is not None
        and isinstance(node.target, functools.partial)
        and len(node.target.args) > 0
        and hasattr(node.target.args[0], "targets")
    ):
        for target in node.target.args[0].targets:
            if target.fns[0] in [
                torch.ops.mkldnn._convolution_pointwise.default,
                torch.ops.mkldnn._convolution_pointwise.binary,
                torch.ops.mkldnn._convolution_pointwise_.binary,
            ]:
                return True

    return False