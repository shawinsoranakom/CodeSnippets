def from_config(cls, config: dict[str, Any]) -> "QuarkConfig":
        export_config = config.get("export")
        if export_config is None:
            raise ValueError(
                "The export key should be included in "
                "the configurations of Quark quantized model"
            )
        kv_cache_group = cast(list[str], export_config.get("kv_cache_group"))
        pack_method = cast(str, export_config.get("pack_method"))

        # In the export model of quark, the quantization configuration
        # of kv_cache is stored in layer_quant_config. First, it is
        # judged whether kv_cache_group exists, and then it is judged
        # whether layer_quant_config has a quantization configuration
        # that matches kv_cache.
        if len(kv_cache_group) == 0:
            kv_cache_config = None
        else:
            kv_cache_set = set(kv_cache_group)
            layer_quant_config = cast(dict[str, Any], config.get("layer_quant_config"))
            layer_quant_names = list(layer_quant_config.keys())
            layer_quant_set = set(layer_quant_names)

            if not (
                kv_cache_set.issubset(layer_quant_set)
                or any(
                    fnmatch.fnmatchcase(layer_quant, pat)
                    for layer_quant in list(layer_quant_set)
                    for pat in list(kv_cache_set)
                )
            ):
                raise ValueError(
                    "The Quark quantized model has the "
                    "kv_cache_group parameter setting, "
                    "but no kv_cache quantization settings "
                    "were found in the quantization "
                    "configuration."
                )

            q_configs = [
                quant_cfg
                for name, quant_cfg in layer_quant_config.items()
                if any(fnmatch.fnmatchcase(name, pattern) for pattern in kv_cache_group)
            ]

            if not all(
                deep_compare(q_config["output_tensors"], q_configs[0]["output_tensors"])
                for q_config in q_configs
            ):
                raise ValueError(
                    "The quantization method used for kv_cache should "
                    "be the same, but the quantization method for the "
                    "kv_cache layer in the config is different."
                )
            kv_cache_config = q_configs[0].get("output_tensors")
            if kv_cache_config is None:
                raise ValueError("The kv_cache quantization configuration is empty.")

            # Since we have already set kv_cache quantization configurations,
            # we will remove the quantization configuration for the
            # output_tensors corresponding to the kv_cache layer.
            for q_config in q_configs:
                q_config["output_tensors"] = None

            # In case q_proj output is also quantized, remove the configuration
            # to keep qkv consistency.
            q_proj_q_config = cast(dict[str, Any], layer_quant_config.get("*q_proj"))
            if q_proj_q_config is not None:
                q_proj_q_config["output_tensors"] = None

        return cls(
            quant_config=config,
            kv_cache_group=kv_cache_group,
            kv_cache_config=kv_cache_config,
            pack_method=pack_method,
        )