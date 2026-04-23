def get_quant_method(
        self, layer: torch.nn.Module, prefix: str
    ) -> "QuantizeMethodBase | None":
        if not isinstance(layer, LinearBase):
            return None

        from torchao.quantization import ModuleFqnToConfig

        if should_skip(prefix, self.skip_modules):
            return UnquantizedLinearMethod()

        module_fqn = prefix
        if isinstance(self.torchao_config, ModuleFqnToConfig):
            module_fqn_to_config = self.torchao_config.module_fqn_to_config
            c = None
            if module_fqn in module_fqn_to_config:
                assert not module_fqn.startswith("re:"), (
                    "module fqn should not start with"
                    "`re:`, which is used for specifying regex"
                )
                c = module_fqn_to_config[module_fqn]
            else:
                for maybe_module_fqn_pattern in module_fqn_to_config:
                    if not maybe_module_fqn_pattern.startswith("re:"):
                        continue
                    elif re.fullmatch(maybe_module_fqn_pattern[3:], module_fqn):
                        # we'll apply the config for first fully matched pattern
                        c = module_fqn_to_config[maybe_module_fqn_pattern]
                        break
                else:
                    # fallback to use default if no module specific
                    # config is provided
                    c = module_fqn_to_config.get("_default", None)

            if c is not None:
                current_torchao_config = TorchAOConfig(
                    c, self.skip_modules, self.is_checkpoint_torchao_serialized
                )
                return TorchAOLinearMethod(current_torchao_config)
            else:
                return UnquantizedLinearMethod()

        return TorchAOLinearMethod(self)