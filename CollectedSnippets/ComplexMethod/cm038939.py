def bench_fn_kwargs(
        self, ctx: BenchmarkContext, op_type: OpType, add_inputs: bool | None = None
    ) -> dict[str, Any]:
        if op_type.is_shrink_fn() or op_type.is_fused_moe_lora_fn():
            assert add_inputs is None
        else:
            assert add_inputs is not None

        if op_type == OpType.LORA_SHRINK:
            return self.as_lora_shrink_kwargs(ctx, op_type)
        if op_type == OpType.LORA_EXPAND:
            return self.as_lora_expand_kwargs(ctx, op_type, add_inputs)
        if op_type.is_fused_moe_lora_shrink_fn():
            return self.as_fused_moe_lora_shrink_kwargs(ctx, op_type)
        if op_type.is_fused_moe_lora_expand_fn():
            return self.as_fused_moe_lora_expand_kwargs(ctx, op_type)
        raise ValueError(f"Unrecognized optype {self}")