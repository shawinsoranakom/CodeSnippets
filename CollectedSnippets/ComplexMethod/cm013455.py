def _maybe_record_pointwise_barrier(
    func: object, proxy_mode: ProxyTorchDispatchMode
) -> None:
    """
    Records operators whose tensor outputs or inputs are fp16/bf16 so downstream pointwise code can
    emulate eager's rounding behavior when emulate_precision_casts is enabled.
    """
    if proxy_mode.decomp_layers or not proxy_mode.emulate_precision_casts:
        return

    if not isinstance(func, torch._ops.OpOverload):
        return

    last_node = next(iter(reversed(proxy_mode.tracer.graph.nodes)))
    t = last_node.meta.get("val")
    low_pr_fp = (torch.bfloat16, torch.float16)

    output_low_precision = isinstance(t, torch.Tensor) and t.dtype in low_pr_fp

    if not output_low_precision:
        for input_node in last_node.all_input_nodes:
            val = input_node.meta.get("val") if hasattr(input_node, "meta") else None
            if isinstance(val, torch.Tensor) and val.dtype in low_pr_fp:
                output_low_precision = True
                break

    if not output_low_precision:
        return

    last_node.meta["low_precision_pointwise_barrier"] = True