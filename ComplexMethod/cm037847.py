def _get_bnb_target_modules(self, model: nn.Module) -> None:
        """
        Identify and collect all modules that support BitsAndBytes
        quantization.
        """
        for name, module in model.named_modules():
            if isinstance(module, LinearBase) and hasattr(
                module.quant_method, "quant_config"
            ):
                if modules_info := self.modules_mapping.get_sub_modules(name):
                    # Map vllm's names to transformers's names.
                    rep_name, sub_modules = modules_info
                    for sub_name in sub_modules:
                        new_name = name.replace(rep_name, sub_name)
                        self.target_modules.append(new_name)
                        if module.disable_tp:
                            self.tp_disabled_modules.append(new_name)
                # Add original module name even if the module has stacked map,
                # in case model has a mixture of disk-merged and disk-split
                # weights with same last name.
                self.target_modules.append(name)
                if module.disable_tp:
                    self.tp_disabled_modules.append(name)
            elif isinstance(module, FusedMoE) and hasattr(
                module.quant_method, "quant_config"
            ):
                # TODO: support FusedMoE with prequant and 8bit.
                if self.pre_quant and self.load_8bit:
                    raise ValueError(
                        "Prequant BitsAndBytes 8bit models with FusedMoE "
                        "is not supported yet."
                    )
                # Get the corresponding weight name using module name and
                # expert_params_mapping.

                for exp in self.expert_params_mapping:
                    weight_name = exp[1]
                    rep_name = name.replace("experts", "") + weight_name.removesuffix(
                        "."
                    )
                    self.target_modules.append(rep_name)

        assert self.target_modules, (
            "vLLM currently does not support BNB quantization for"
        )
        f" {type(model).__name__}"