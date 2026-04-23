def get_loop_body_lowp_fp(_body: LoopBody) -> tuple[torch.dtype | None, bool]:
    """
    Returns the low precision data type (torch.float16/torch.bfloat16) contained in the nodes
    and if all the nodes can codegen with this data type without converting to float.
    Otherwise returns None and True.
    """
    sub_blocks = [_body.root_block] + list(_body.subblocks.values())

    _lowp_fp_type: torch.dtype | None = None
    _use_fp32 = False
    for sub_block in sub_blocks:
        for _node in sub_block.graph.nodes:
            if _node.op == "placeholder" or _node.target in (
                "get_index",
                "index_expr",
            ):
                continue

            # Fast path if all operations can support bf16/fp16 without converting to fp32
            if _node.target not in [
                "load",
                "store",
                "abs",
                "neg",
                "output",
            ]:
                _use_fp32 = True

            if hasattr(_node, "meta") and _node.meta:
                assert OptimizationContext.key in _node.meta
                opt_ctx: OptimizationContext = _node.meta[OptimizationContext.key]
                if not opt_ctx.dtype or opt_ctx.dtype not in DTYPE_LOWP_FP:
                    _use_fp32 = True
                elif _lowp_fp_type is not None:
                    if _lowp_fp_type != opt_ctx.dtype:
                        warnings.warn("bf16 and fp16 are mixed in the scheduler node.")
                else:
                    _lowp_fp_type = opt_ctx.dtype
            else:
                _use_fp32 = True

    return _lowp_fp_type, _use_fp32