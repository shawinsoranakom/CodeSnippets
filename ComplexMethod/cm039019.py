def group_trace_by_operations(trace_df: "pd.DataFrame") -> "pd.DataFrame":
    def is_rms_norm(op_name: str):
        if "rms_norm_kernel" in op_name:
            return True

    def is_attention_block(op_name: str):
        if "flash_fwd" in op_name or "reshape_and_cache_flash_kernel" in op_name:
            return True

    def is_quant(op_name: str):
        if "scaled_fp8_quant" in op_name or "scaled_int8_quant" in op_name:
            return True

    # LoRA ops
    def is_sgmv_shrink(op_name: str):
        return "sgmv_shrink" in op_name

    def is_sgmv_expand(op_name: str):
        return "sgmv_expand" in op_name

    def is_bgmv_shrink(op_name: str):
        return "bgmv_shrink" in op_name

    def is_bgmv_expand(op_name: str):
        return "bgmv_expand" in op_name

    def is_cutlass_gemm_op(op_name: str):
        return (
            "void cutlass::Kernel" in op_name
            or "void cutlass::device_kernel" in op_name
        )

    def is_gemm_op(op_name: str):
        if is_quant(op_name):
            return False
        return (
            is_cutlass_gemm_op(op_name)
            or "xmma_gemm" in op_name
            or "gemv2T_kernel" in op_name
            or "splitKreduce" in op_name
            or "s16816gemm" in op_name
        )

    def is_elementwise_op(op_name: str):
        return "elementwise_kernel" in op_name

    def is_mem_op(op_name: str):
        return "memcpy" in op_name.lower() or "memset" in op_name.lower()

    def is_vocab_embedding_op(op_name: str):
        return "vocabparallelembed" in op_name.lower()

    # nccl ops
    def is_nccl_op(op_name: str):
        return "nccl" in op_name.lower()

    def is_nccl_all_reduce(op_name: str):
        return is_nccl_op(op_name) and (
            "all_reduce" in op_name.lower() or "allreduce" in op_name.lower()
        )

    def is_nccl_gather(op_name: str):
        return is_nccl_op(op_name) and "gather" in op_name.lower()

    def is_nccl_broadcast(op_name: str):
        return is_nccl_op(op_name) and "broadcast" in op_name.lower()

    # Reduce ops types
    def is_cross_device_reduce_1stage(op_name: str):
        return "cross_device_reduce_1stage" in op_name

    def is_cross_device_reduce_2stage(op_name: str):
        return "cross_device_reduce_2stage" in op_name

    def is_custom_ar_all_reduce(op_name: str):
        return "_C_custom_ar::all_reduce" in op_name

    def is_reduce_kernel(op_name: str):
        return "reduce_kernel" in op_name

    headers = list(trace_df)
    ops = copy.deepcopy(headers)

    attention_ops = list(filter(lambda x: is_attention_block(x), ops))
    ops = list(filter(lambda x: x not in attention_ops, ops))

    quant_ops = list(filter(lambda x: is_quant(x), ops))
    ops = list(filter(lambda x: x not in quant_ops, ops))

    sgmv_shrink_ops = list(filter(lambda x: is_sgmv_shrink(x), ops))
    ops = list(filter(lambda x: x not in sgmv_shrink_ops, ops))
    sgmv_expand_ops = list(filter(lambda x: is_sgmv_expand(x), ops))
    ops = list(filter(lambda x: x not in sgmv_expand_ops, ops))
    bgmv_shrink_ops = list(filter(lambda x: is_bgmv_shrink(x), ops))
    ops = list(filter(lambda x: x not in bgmv_shrink_ops, ops))
    bgmv_expand_ops = list(filter(lambda x: is_bgmv_expand(x), ops))
    ops = list(filter(lambda x: x not in bgmv_expand_ops, ops))

    cutlass_gemm_ops = list(filter(lambda x: is_cutlass_gemm_op(x), ops))
    ops = list(filter(lambda x: x not in cutlass_gemm_ops, ops))

    gemm_ops = list(filter(lambda x: is_gemm_op(x), ops))
    ops = list(filter(lambda x: x not in gemm_ops, ops))

    rms_norm_ops = list(filter(lambda x: is_rms_norm(x), ops))
    ops = list(filter(lambda x: x not in rms_norm_ops, ops))

    vocab_embed_ops = list(filter(lambda x: is_vocab_embedding_op(x), ops))
    ops = list(filter(lambda x: x not in vocab_embed_ops, ops))

    mem_ops = list(filter(lambda x: is_mem_op(x), ops))
    ops = list(filter(lambda x: x not in mem_ops, ops))

    elementwise_ops = list(filter(lambda x: is_elementwise_op(x), ops))
    ops = list(filter(lambda x: x not in elementwise_ops, ops))

    nccl_all_reduce_ops = list(filter(lambda x: is_nccl_all_reduce(x), ops))
    ops = list(filter(lambda x: x not in nccl_all_reduce_ops, ops))

    nccl_gather_ops = list(filter(lambda x: is_nccl_gather(x), ops))
    ops = list(filter(lambda x: x not in nccl_gather_ops, ops))

    nccl_broadcast_ops = list(filter(lambda x: is_nccl_broadcast(x), ops))
    ops = list(filter(lambda x: x not in nccl_broadcast_ops, ops))

    nccl_other_ops = list(filter(lambda x: is_nccl_op(x), ops))
    ops = list(filter(lambda x: x not in nccl_other_ops, ops))

    cross_device_reduce_1stage_ops = list(
        filter(lambda x: is_cross_device_reduce_1stage(x), ops)
    )
    ops = list(filter(lambda x: x not in cross_device_reduce_1stage_ops, ops))

    cross_device_reduce_2stage_ops = list(
        filter(lambda x: is_cross_device_reduce_2stage(x), ops)
    )
    ops = list(filter(lambda x: x not in cross_device_reduce_2stage_ops, ops))

    custom_ar_all_reduce_ops = list(filter(lambda x: is_custom_ar_all_reduce(x), ops))
    ops = list(filter(lambda x: x not in custom_ar_all_reduce_ops, ops))

    reduce_kernel_ops = list(filter(lambda x: is_reduce_kernel(x), ops))
    ops = list(filter(lambda x: x not in reduce_kernel_ops, ops))

    if len(attention_ops):
        trace_df["attention"] = trace_df[attention_ops].agg("sum", axis=1)
    if len(quant_ops):
        trace_df["quant_ops"] = trace_df[quant_ops].agg("sum", axis=1)

    if len(sgmv_shrink_ops):
        trace_df["sgmv_shrink_ops"] = trace_df[sgmv_shrink_ops].agg("sum", axis=1)
    if len(sgmv_expand_ops):
        trace_df["sgmv_expand_ops"] = trace_df[sgmv_expand_ops].agg("sum", axis=1)
    if len(bgmv_shrink_ops):
        trace_df["bgmv_shrink_ops"] = trace_df[bgmv_shrink_ops].agg("sum", axis=1)
    if len(bgmv_expand_ops):
        trace_df["bgmv_expand_ops"] = trace_df[bgmv_expand_ops].agg("sum", axis=1)

    if len(cutlass_gemm_ops):
        trace_df["cutlass_gemm_ops"] = trace_df[cutlass_gemm_ops].agg("sum", axis=1)

    if len(gemm_ops):
        trace_df["gemm_ops"] = trace_df[gemm_ops].agg("sum", axis=1)
    if len(rms_norm_ops):
        trace_df["rms_norm_ops"] = trace_df[rms_norm_ops].agg("sum", axis=1)
    if len(vocab_embed_ops):
        trace_df["vocab_embed_ops"] = trace_df[vocab_embed_ops].agg("sum", axis=1)
    if len(mem_ops):
        trace_df["mem_ops"] = trace_df[mem_ops].agg("sum", axis=1)
    if len(elementwise_ops):
        trace_df["elementwise_ops"] = trace_df[elementwise_ops].agg("sum", axis=1)

    if len(nccl_all_reduce_ops):
        trace_df["nccl_all_reduce_ops"] = trace_df[nccl_all_reduce_ops].agg(
            "sum", axis=1
        )
    if len(nccl_gather_ops):
        trace_df["nccl_gather_ops"] = trace_df[nccl_gather_ops].agg("sum", axis=1)
    if len(nccl_broadcast_ops):
        trace_df["nccl_broadcast_ops"] = trace_df[nccl_broadcast_ops].agg("sum", axis=1)
    if len(nccl_other_ops):
        trace_df["nccl_other_ops"] = trace_df[nccl_other_ops].agg("sum", axis=1)

    if len(cross_device_reduce_1stage_ops):
        trace_df["cross_device_reduce_1stage_ops"] = trace_df[
            cross_device_reduce_1stage_ops
        ].agg("sum", axis=1)
    if len(cross_device_reduce_2stage_ops):
        trace_df["cross_device_reduce_2stage_ops"] = trace_df[
            cross_device_reduce_2stage_ops
        ].agg("sum", axis=1)
    if len(custom_ar_all_reduce_ops):
        trace_df["custom_ar_all_reduce_ops"] = trace_df[custom_ar_all_reduce_ops].agg(
            "sum", axis=1
        )
    if len(reduce_kernel_ops):
        trace_df["reduce_kernel_ops"] = trace_df[reduce_kernel_ops].agg("sum", axis=1)

    trace_df.drop(
        attention_ops
        + quant_ops
        + sgmv_shrink_ops
        + sgmv_expand_ops
        + bgmv_shrink_ops
        + bgmv_expand_ops
        + cutlass_gemm_ops
        + gemm_ops
        + rms_norm_ops
        + vocab_embed_ops
        + mem_ops
        + elementwise_ops
        + nccl_all_reduce_ops
        + nccl_gather_ops
        + nccl_broadcast_ops
        + nccl_other_ops
        + cross_device_reduce_1stage_ops
        + cross_device_reduce_2stage_ops
        + custom_ar_all_reduce_ops
        + reduce_kernel_ops,
        axis=1,
        inplace=True,
    )
    return trace_df