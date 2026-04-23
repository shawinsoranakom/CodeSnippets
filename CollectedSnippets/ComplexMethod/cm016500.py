def _load_list(self, for_dynamic=False, default_device=None):
        loading = []
        for n, m in self.model.named_modules():
            default = False
            params = { name: param for name, param in m.named_parameters(recurse=False) }
            for name, param in m.named_parameters(recurse=True):
                if name not in params:
                    default = True # default random weights in non leaf modules
                    break
            if default and default_device is not None:
                for param_name, param in params.items():
                    param.data = param.data.to(device=default_device, dtype=getattr(m, param_name + "_comfy_model_dtype", None))
            if not default and (hasattr(m, "comfy_cast_weights") or len(params) > 0):
                module_mem = comfy.model_management.module_size(m)
                module_offload_mem = module_mem
                if hasattr(m, "comfy_cast_weights"):
                    def check_module_offload_mem(key):
                        if key in self.patches:
                            return low_vram_patch_estimate_vram(self.model, key)
                        model_dtype = getattr(self.model, "manual_cast_dtype", None)
                        weight, _, _ = get_key_weight(self.model, key)
                        if model_dtype is None or weight is None:
                            return 0
                        if (weight.dtype != model_dtype or isinstance(weight, QuantizedTensor)):
                            return weight.numel() * model_dtype.itemsize
                        return 0
                    module_offload_mem += check_module_offload_mem("{}.weight".format(n))
                    module_offload_mem += check_module_offload_mem("{}.bias".format(n))
                # Dynamic: small weights (<64KB) first, then larger weights prioritized by size.
                # Non-dynamic: prioritize by module offload cost.
                if for_dynamic:
                    sort_criteria = (module_offload_mem >= 64 * 1024, -module_offload_mem)
                else:
                    sort_criteria = (module_offload_mem,)
                loading.append(sort_criteria + (module_mem, n, m, params))
        return loading