def _init_weights(self, module):
        if isinstance(module, nn.Embedding):
            small_init_method(self.config.hidden_size)(self.embeddings.weight)
        elif isinstance(module, nn.Linear):
            if module.bias is not None:
                init.zeros_(module.bias)
            if self.config.weight_mode == "single" and "gate" in self._module_name_map(module):
                init.zeros_(module.weight)

                if "igate" in self._module_name_map(module):
                    init.copy_(module.bias, -10.0 * torch.ones_like(module.bias))
                elif "fgate" in self._module_name_map(module):
                    init.copy_(
                        module.bias,
                        torch.linspace(
                            3.0,
                            6.0,
                            module.bias.shape[-1],
                        ).to(
                            device=module.bias.device,
                            dtype=module.bias.dtype,
                        ),
                    )
            elif self.config.weight_mode == "fused" and "gate" in self._module_name_map(module):
                init.zeros_(module.weight)

                init.copy_(
                    module.bias[: self.config.num_heads],
                    module.bias[: self.config.num_heads]
                    - module.bias[: self.config.num_heads]
                    - 10.0 * torch.ones_like(module.bias),
                )
                init.copy_(
                    module.bias[: self.config.num_heads],
                    module.bias[: self.config.num_heads]
                    - module.bias[self.config.num_heads :]
                    + torch.linspace(
                        3.0,
                        6.0,
                        module.bias.shape[-1],
                    ).to(
                        device=module.bias.device,
                        dtype=module.bias.dtype,
                    ),
                )
            elif "proj_down" in self._module_name_map(module):
                wang_init_method(dim=module.weight.shape[1], n_layers=self.config.num_hidden_layers)(module.weight)
            elif "out_proj" in self._module_name_map(module):
                wang_init_method(dim=self.config.hidden_size, n_layers=self.config.num_hidden_layers)(module.weight)
            elif module.weight is not None:
                small_init_method(self.config.hidden_size)(module.weight)
        elif isinstance(module, xLSTMRMSNorm) or hasattr(module, "_layer_normalize"):
            init.ones_(module.weight)
            if hasattr(module, "bias") and module.bias is not None:
                init.zeros_(module.bias)