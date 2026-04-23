def _finalize_mm_configs(
        self,
        configs: list[BaseConfig],
    ) -> Generator[TritonConfig, None, None]:
        """
        Finalizes configs after scaling, applying additional constraints.
        """
        used: OrderedSet[tuple[int | None, ...]] = OrderedSet()

        max_mm_configs = config.test_configs.max_mm_configs

        for conf in configs:
            # Each warp computes a 16x16 tile = 256 elements
            num_warps = min(conf.num_warps, conf.block_m * conf.block_n // 256)

            # Construct key for finding duplicate configs
            key: tuple[int | None, ...] = (
                conf.block_m,
                conf.block_n,
                conf.block_k,
                conf.num_stages,
                conf.hint_override,
                num_warps,
            )

            # Check if gemm specific arg exists - add to key if does
            group_m = getattr(conf, "group_m", None)
            if group_m is not None:
                key += (group_m,)

            # Add BlackwellGPUGemmConfig specific fields to key if present
            if isinstance(conf, BlackwellGPUGemmConfig):
                key += (conf.epilogue_subtile, conf.warp_specialize, conf.flatten)

            extra_key, extra_kwargs = self._get_extra_config_key_and_kwargs(conf)
            key += extra_key

            if key not in used and (
                max_mm_configs is None or len(used) < max_mm_configs
            ):
                used.add(key)
                kwargs: dict[str, Any] = {
                    "BLOCK_M": conf.block_m,
                    "BLOCK_N": conf.block_n,
                    "BLOCK_K": conf.block_k,
                    "hint_override": conf.hint_override,
                }
                if group_m is not None:
                    kwargs["GROUP_M"] = group_m

                # Add BlackwellGPUGemmConfig specific fields if present
                if isinstance(conf, BlackwellGPUGemmConfig):
                    kwargs["EPILOGUE_SUBTILE"] = conf.epilogue_subtile
                    kwargs["WARP_SPECIALIZE"] = conf.warp_specialize
                    kwargs["FLATTEN"] = conf.flatten

                kwargs.update(extra_kwargs)

                yield self.triton_config(conf.num_stages, num_warps, **kwargs)