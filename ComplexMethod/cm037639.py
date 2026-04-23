def _quantization_scheme_map_from_config(
        cls, config: dict[str, Any]
    ) -> QUANTIZATION_SCHEME_MAP_TYPE:
        """
        :param config: The `quantization_config` dictionary from config.json
        :return: A dictionary mapping target layer names to their corresponding
            quantization_args for weights and input activations
        """
        target_scheme_map: dict[str, Any] = dict()
        quant_format = cast(str, config.get("format"))

        # The quant_config has multiple config_groups, each containing
        # an input_activations key with details about how the activations are
        # quantized, a weights key indicating how the weights are quantized,
        # and a list of targets under the `targets` key, dictating which
        # layers are impacted by the quantization details. The quantization
        # details follow the structure defined by the QuantizationArgs
        # pydantic model, which is used to verify the structure of the
        # quant_config and also store the details for later use.

        config_groups = config.get("config_groups", dict())
        for _, quant_config in config_groups.items():
            targets = quant_config.get("targets")
            for target in targets:
                target_scheme_map[target] = {}
                target_scheme_map[target]["weights"] = QuantizationArgs.model_validate(
                    quant_config.get("weights")
                )

                target_scheme_map[target]["input_activations"] = None
                target_scheme_map[target]["format"] = quant_config.get("format")
                format = target_scheme_map[target].get("format")
                # If no per-config format defined, use global format in config
                act_quant_format = (
                    is_activation_quantization_format(format)
                    if format is not None
                    else is_activation_quantization_format(quant_format)
                )
                # w4a8fp8 is in packed-quantized format
                # but needs input activation quantization
                input_activations = quant_config.get("input_activations")
                if act_quant_format or input_activations:
                    # The only case where we have activation quant supported
                    # but no input_activations provided in the config
                    # should be w8a16fp8 w8a16fp8 can also run for cases where
                    # there is an input_quant but it is ignored
                    if not input_activations:
                        assert (
                            target_scheme_map[target]["weights"].type
                            == QuantizationType.FLOAT
                        )
                    else:
                        target_scheme_map[target]["input_activations"] = (
                            QuantizationArgs.model_validate(
                                quant_config.get("input_activations")
                            )
                        )
        return target_scheme_map