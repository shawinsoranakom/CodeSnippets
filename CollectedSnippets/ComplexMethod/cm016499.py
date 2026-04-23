def patch_weight_to_device(self, key, device_to=None, inplace_update=False, return_weight=False, force_cast=False):
        weight, set_func, convert_func = get_key_weight(self.model, key)
        if key not in self.patches and not force_cast:
            return weight

        inplace_update = self.weight_inplace_update or inplace_update

        if key not in self.backup and not return_weight:
            self.backup[key] = collections.namedtuple('Dimension', ['weight', 'inplace_update'])(weight.to(device=self.offload_device, copy=inplace_update), inplace_update)

        temp_dtype = comfy.model_management.lora_compute_dtype(device_to) if key in self.patches else None
        if device_to is not None:
            temp_weight = comfy.model_management.cast_to_device(weight, device_to, temp_dtype, copy=True)
        else:
            temp_weight = weight.to(temp_dtype, copy=True)
        if convert_func is not None:
            temp_weight = convert_func(temp_weight, inplace=True)

        out_weight = comfy.lora.calculate_weight(self.patches[key], temp_weight, key) if key in self.patches else temp_weight
        if set_func is None:
            if key in self.patches:
                out_weight = comfy.float.stochastic_rounding(out_weight, weight.dtype, seed=comfy.utils.string_to_seed(key))
            if return_weight:
                return out_weight
            elif inplace_update:
                comfy.utils.copy_to_param(self.model, key, out_weight)
            else:
                comfy.utils.set_attr_param(self.model, key, out_weight)
        else:
            return set_func(out_weight, inplace_update=inplace_update, seed=comfy.utils.string_to_seed(key), return_weight=return_weight)