def _verify_quantization(self) -> None:
        supported_quantization = me_quant.QUANTIZATION_METHODS
        if self.quantization is not None:
            self.quantization = cast(me_quant.QuantizationMethods, self.quantization)

        # Parse quantization method from the HF model config, if available.
        quant_cfg = self.model_arch_config.quantization_config

        if quant_cfg is not None:
            quant_method = quant_cfg["quant_method"]
            # Quantization methods which are overrides (i.e. they have a
            # `override_quantization_method` method) must be checked in order
            # of preference (this is particularly important for GPTQ).
            overrides = [
                "gptq_marlin",
                "awq_marlin",
                "inc",
                "moe_wna16",
                "modelopt",
                "modelopt_fp4",
                "modelopt_mxfp8",
                "modelopt_mixed",
                # Ensure heavy backends are probed last to avoid unnecessary
                # imports during override detection (e.g., MXFP4 imports Triton)
                "mxfp4",
                "gpt_oss_mxfp4",
                "cpu_awq",
                "gguf",
            ]
            quantization_methods = [
                q for q in supported_quantization if q not in overrides
            ]
            # Any custom overrides will be in quantization_methods so we place
            # them at the start of the list so custom overrides have preference
            # over the built-in ones.
            quantization_methods = quantization_methods + overrides

            # Detect which checkpoint is it
            for name in quantization_methods:
                method = me_quant.get_quantization_config(name)
                quantization_override = method.override_quantization_method(
                    quant_cfg, self.quantization, hf_config=self.hf_config
                )
                if quantization_override is not None:
                    # Raise error if the override is not custom (custom would
                    # be in QUANTIZATION_METHODS but not QuantizationMethods)
                    # and hasn't been added to the overrides list.
                    if (
                        name in get_args(me_quant.QuantizationMethods)
                        and name not in overrides
                    ):
                        raise ValueError(
                            f"Quantization method {name} is an override but "
                            "is has not been added to the `overrides` list "
                            "above. This is necessary to ensure that the "
                            "overrides are checked in order of preference."
                        )
                    quant_method = quantization_override
                    self.quantization = quantization_override
                    break

            quant_method = quant_method if quant_method != "" else None
            # Verify quantization configurations.
            if self.quantization is None:
                self.quantization = quant_method
            elif self.quantization != quant_method:
                raise ValueError(
                    "Quantization method specified in the model config "
                    f"({quant_method}) does not match the quantization "
                    f"method specified in the `quantization` argument "
                    f"({self.quantization})."
                )

        if self.quantization is not None:
            if self.quantization not in supported_quantization:
                raise ValueError(
                    f"Unknown quantization method: {self.quantization}. Must "
                    f"be one of {supported_quantization}."
                )
            current_platform.verify_quantization(self.quantization)

        if self.quantization in me_quant.DEPRECATED_QUANTIZATION_METHODS:
            if self.allow_deprecated_quantization:
                logger.warning(
                    "The quantization method %s is deprecated "
                    "and will be removed in future versions of vLLM.",
                    self.quantization,
                )
            else:
                raise ValueError(
                    "The quantization method %s is deprecated "
                    "and will be removed in future versions of vLLM. To bypass, "
                    "set `--allow-deprecated-quantization`.",
                    self.quantization,
                )