def fast_lora_forward(self, x: torch.Tensor, *args, **kwargs) -> torch.Tensor:
    raise NotImplementedError(
        "Unsloth: Currently not supported yet - reshaping done incorrectly"
    )
    self._check_forward_args(x, *args, **kwargs)
    adapter_names = kwargs.pop("adapter_names", None)

    if self.disable_adapters:
        if self.merged:
            self.unmerge()
        result = self.base_layer(x, *args, **kwargs)
    elif adapter_names is not None:
        result = self._mixed_batch_forward(
            x, *args, adapter_names = adapter_names, **kwargs
        )
    elif self.merged:
        result = self.base_layer(x, *args, **kwargs)
    else:
        # Fastpath
        if len(self.active_adapters) == 1:
            active_adapter = self.active_adapters[0]
            if active_adapter not in self.lora_A.keys():
                return self.base_layer(x, *args, **kwargs)

            dropout = self.lora_dropout[active_adapter]
            if (
                isinstance(dropout, IDENTITY_DROPOUT)
                and not self.use_dora[active_adapter]
            ):
                lora_A = self.lora_A[active_adapter].weight
                lora_B = self.lora_B[active_adapter].weight
                scaling = self.scaling[active_adapter]
                W = self.base_layer.weight
                return LoRA_W.apply(x, W, QUANT_STATE(W), lora_A, lora_B, scaling)
            pass
        pass

        result = self.base_layer(x, *args, **kwargs)
        # As per Tim Dettmers, for 4bit, we need to defensively clone here.
        # The reason is that in some cases, an error can occur that backprop
        # does not work on a manipulated view. This issue may be solved with
        # newer PyTorch versions but this would need extensive testing to be
        # sure.
        result = result.clone()

        for active_adapter in self.active_adapters:
            if active_adapter not in self.lora_A.keys():
                continue
            lora_A = self.lora_A[active_adapter]
            lora_B = self.lora_B[active_adapter]
            dropout = self.lora_dropout[active_adapter]
            scaling = self.scaling[active_adapter]

            requires_conversion = not torch.is_autocast_enabled()
            if requires_conversion:
                expected_dtype = result.dtype
                x = x.to(lora_A.weight.dtype)

            if not self.use_dora[active_adapter]:
                result = result + lora_B(lora_A(dropout(x))) * scaling
            else:
                if isinstance(dropout, torch.nn.Identity) or not self.training:
                    base_result = result
                else:
                    x = dropout(x)
                    base_result = None

                result = result + self.lora_magnitude_vector[active_adapter](
                    x,
                    lora_A = lora_A,
                    lora_B = lora_B,
                    scaling = scaling,
                    base_layer = self.get_base_layer(),
                    base_result = base_result,
                )
            if requires_conversion:
                result = result.to(expected_dtype)

    return result