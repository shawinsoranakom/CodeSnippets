def load_from_state_dict(original, module, state_dict, prefix, *args, **kwargs):
            used_param_keys = []

            for name, param in module._parameters.items():
                if param is None:
                    continue

                key = prefix + name
                sd_param = sd.pop(key, None)
                if sd_param is not None:
                    state_dict[key] = sd_param.to(dtype=self.get_weight_dtype(key))
                    used_param_keys.append(key)

                if param.is_meta:
                    dtype = sd_param.dtype if sd_param is not None else param.dtype
                    module._parameters[name] = torch.nn.parameter.Parameter(torch.zeros_like(param, device=device, dtype=dtype), requires_grad=param.requires_grad)

            for name in module._buffers:
                key = prefix + name

                sd_param = sd.pop(key, None)
                if sd_param is not None:
                    state_dict[key] = sd_param
                    used_param_keys.append(key)

            original(module, state_dict, prefix, *args, **kwargs)

            for key in used_param_keys:
                state_dict.pop(key, None)