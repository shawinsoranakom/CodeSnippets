def _resolve_quant_algo(self, prefix: str) -> str | None:
        """Look up the quant_algo for a vLLM-side layer prefix.

        Tries three strategies in order:
        1. Direct lookup in ``quantized_layers``.
        2. Packed/fused-layer lookup (unfuse via ``packed_modules_mapping``).
        3. Prefix-based lookup for FusedMoE (any child key starts with
           ``prefix + "."``).

        Returns the upper-cased quant_algo string, or *None* if the prefix
        is not found.
        """
        # 1. Direct lookup
        if prefix in self.quantized_layers:
            return self.quantized_layers[prefix]["quant_algo"].upper()

        # 2. Packed / fused layer lookup
        proj_name = prefix.rsplit(".", 1)[-1]
        if self.packed_modules_mapping and proj_name in self.packed_modules_mapping:
            algos: set[str] = set()
            base = prefix.rsplit(".", 1)[0]
            for shard_name in self.packed_modules_mapping[proj_name]:
                shard_prefix = f"{base}.{shard_name}"
                if shard_prefix in self.quantized_layers:
                    algos.add(self.quantized_layers[shard_prefix]["quant_algo"].upper())
            if len(algos) == 1:
                return algos.pop()
            if len(algos) > 1:
                raise ValueError(
                    f"Mixed quant_algo within fused layer {prefix}: "
                    f"{algos}. All shards must use the same quantization."
                )

        # 3. Prefix-based lookup (for FusedMoE / parent modules)
        prefix_dot = prefix + "."
        for key, info in self.quantized_layers.items():
            if key.startswith(prefix_dot):
                return info["quant_algo"].upper()

        return None