def _test_validate_frozen_params(self, use_orig_params: bool):
        model = LoraModel()
        # Wrap only LoRA modules
        modules_to_wrap = {
            module
            for module_name, module in model.named_modules()
            if "lora_A" in module_name or "lora_B" in module_name
        }
        _validate_frozen_params(model, modules_to_wrap, set(), use_orig_params)
        # Additionally wrap attention
        for module in model.modules():
            if isinstance(module, LoraAttention):
                modules_to_wrap.add(module)
        _validate_frozen_params(model, modules_to_wrap, set(), use_orig_params)
        # Additionally wrap decoders
        for module in model.modules():
            if isinstance(module, LoraDecoder):
                modules_to_wrap.add(module)
        _validate_frozen_params(model, modules_to_wrap, set(), use_orig_params)
        # Do not wrap the LoRA-A modules (meaning mixed frozen/non-frozen)
        for module_name, module in model.named_modules():
            if "lora_A" in module_name:
                modules_to_wrap.remove(module)
        regex = "layers.0.attn has both parameters with requires_grad=True and False."
        if use_orig_params:
            # Wrapping the attention manages all parameters except those from
            # the LoRA-B module, which is separately wrapped and all nonfrozen
            lorab_numel = sum(
                p.numel() for p in model.layers[0].attn.lora_B.parameters()
            )
            attn_frozen_param_numel = sum(
                p.numel()
                for p in model.layers[0].attn.parameters()
                if not p.requires_grad
            )
            attn_nonfrozen_param_numel = (
                sum(
                    p.numel()
                    for p in model.layers[0].attn.parameters()
                    if p.requires_grad
                )
                - lorab_numel
            )
            attn_total_param_numel = (
                attn_frozen_param_numel + attn_nonfrozen_param_numel
            )
            regex += (
                " We do not recommend wrapping such modules since the "
                r"gradient memory usage will be higher than expected \("
                f"{attn_total_param_numel} numel instead of {attn_nonfrozen_param_numel} numel "
                r"before sharding via reduce-scatter\). "
            )
        else:
            regex += " FSDP does not support wrapping such modules when use_orig_params=False. "
        regex += "If possible, wrap the frozen parameters with FSDP separately.\n"
        regex += (
            "The following parameters have requires_grad=True:\n"
            r"\['layers.0.attn.lora_A.weight'\]\n"
            "The following parameters have requires_grad=False:\n"
            r"\['layers.0.attn.q_proj.weight', 'layers.0.attn.k_proj.weight', "
            r"'layers.0.attn.v_proj.weight', 'layers.0.attn.o_proj.weight'\]"
        )
        if use_orig_params:
            ctx = self.assertWarnsRegex(UserWarning, regex)
        else:
            ctx = self.assertRaisesRegex(ValueError, regex)
        with ctx:
            _validate_frozen_params(model, modules_to_wrap, set(), use_orig_params)
        # Now ignore those LoRA-A modules' parameters
        ignored_params = set()
        for module_name, module in model.named_modules():
            if "lora_A" in module_name:
                ignored_params.update(module.parameters())
        _validate_frozen_params(model, modules_to_wrap, ignored_params, use_orig_params)