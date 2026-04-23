def is_impure(self, node: torch.fx.node.Node) -> bool:
        def is_woq_int8_pattern(node: torch.fx.node.Node) -> bool:
            return (
                node.target is torch.ops.prims.convert_element_type.default  # type: ignore[return-value]
                and isinstance(node.args[0], torch.fx.Node)
                and "val" in node.args[0].meta
                and node.args[0].meta["val"].dtype == torch.int8  # type: ignore[union-attr]
                and node.args[1] == torch.bfloat16
            )

        if (
            is_woq_int8_pattern(node)
            or (
                node.target is torch.ops.aten.permute.default
                and len(node.users) == 1
                and is_woq_int8_pattern(next(iter(node.users)))
            )
        ) and is_const_source(
            node.args[0],  # type: ignore[arg-type]
            self.lifted_constant_names,
        ):
            # Case 1: int8_weight -> dq -> bf16_weight
            # Case 2: int8_weight -> permute -> dq -> bf16_weight
            return True

        quant_registered = (
            getattr(torch.ops.quantized_decomposed, "dequantize_per_channel", None)
            is not None
        )
        if quant_registered and node.target in [
            torch.ops.quantized_decomposed.dequantize_per_channel.default,
            torch.ops.quantized_decomposed.dequantize_per_tensor.default,
            torch.ops.quantized_decomposed.dequantize_per_tensor.tensor,
            torch.ops.quantized_decomposed.convert_element_type.no_fuse,
        ]:
            # For the pattern fp32_weight -> q -> dq
            # We only folding fp32_weight -> q
            # int8_weight and leave dq in graph to be fused
            return True

        if node.target in _dont_constant_fold:
            return True
        return False