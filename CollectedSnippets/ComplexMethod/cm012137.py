def _scale_mm_configs(
        self,
        m: int,
        n: int,
        k: int,
        configs: list[BaseConfig],
        scale: float,
        has_int8_tensor: bool,
        exclude: Callable[[sympy.Integer, sympy.Integer, sympy.Integer], bool],
        hint_override: int | None = None,
    ) -> list[BaseConfig]:
        """
        Scales and filters matrix multiplication configs based on input size.
        """
        if not self.should_scale_configs:
            return configs
        from ..runtime.runtime_utils import next_power_of_2

        min_block_size = 16
        min_block_size_k = 32 if (has_int8_tensor or self.has_int8_tensor) else 16

        scaled_configs = []
        for hint_override in [None] + config.multi_kernel_hints:
            m_hint = max(
                next_power_of_2(
                    V.graph.sizevars.optimization_hint_with_override(
                        m,
                        hint_override=hint_override,
                    )
                ),
                min_block_size,
            )
            n_hint = max(
                next_power_of_2(
                    V.graph.sizevars.optimization_hint_with_override(
                        n,
                        hint_override=hint_override,
                    )
                ),
                min_block_size,
            )
            k_hint = max(
                next_power_of_2(
                    V.graph.sizevars.optimization_hint_with_override(
                        k,
                        hint_override=hint_override,
                    )
                ),
                min_block_size_k,
            )

            for c in configs:
                block_m = max(min(int(c.block_m * scale), m_hint), min_block_size)
                block_n = max(min(int(c.block_n * scale), n_hint), min_block_size)
                block_k = max(min(int(c.block_k * scale), k_hint), min_block_size_k)
                if not exclude(block_m, block_n, block_k):
                    # This copy is expensive, so avoid it if we can.
                    if (block_m, block_n, block_k, hint_override) != (
                        c.block_m,
                        c.block_n,
                        c.block_k,
                        c.hint_override,
                    ):
                        c = dataclasses.replace(
                            c,
                            block_m=block_m,
                            block_n=block_n,
                            block_k=block_k,
                            hint_override=hint_override,
                        )

                    scaled_configs.append(c)

        return scaled_configs