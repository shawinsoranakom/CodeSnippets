def patch_hook_weight_to_device(self, hooks: comfy.hooks.HookGroup, combined_patches: dict, key: str, original_weights: dict, memory_counter: MemoryCounter):
        if key not in combined_patches:
            return

        weight, set_func, convert_func = get_key_weight(self.model, key)
        weight: torch.Tensor
        if key not in self.hook_backup:
            target_device = self.offload_device
            if self.hook_mode == comfy.hooks.EnumHookMode.MaxSpeed:
                used = memory_counter.use(weight)
                if used:
                    target_device = weight.device
            self.hook_backup[key] = (weight.to(device=target_device, copy=True), weight.device)
        # TODO: properly handle LowVramPatch, if it ends up an issue
        temp_weight = comfy.model_management.cast_to_device(weight, weight.device, torch.float32, copy=True)
        if convert_func is not None:
            temp_weight = convert_func(temp_weight, inplace=True)

        out_weight = comfy.lora.calculate_weight(combined_patches[key],
                                                 temp_weight,
                                                 key, original_weights=original_weights)
        del original_weights[key]
        if set_func is None:
            out_weight = comfy.float.stochastic_rounding(out_weight, weight.dtype, seed=comfy.utils.string_to_seed(key))
            comfy.utils.copy_to_param(self.model, key, out_weight)
        else:
            set_func(out_weight, inplace_update=True, seed=comfy.utils.string_to_seed(key))
        if self.hook_mode == comfy.hooks.EnumHookMode.MaxSpeed:
            # TODO: disable caching if not enough system RAM to do so
            target_device = self.offload_device
            used = memory_counter.use(weight)
            if used:
                target_device = weight.device
            self.cached_hook_patches.setdefault(hooks, {})
            self.cached_hook_patches[hooks][key] = (out_weight.to(device=target_device, copy=False), weight.device)
        del temp_weight
        del out_weight
        del weight