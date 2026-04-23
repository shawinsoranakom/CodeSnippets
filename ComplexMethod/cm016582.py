def _lazy_load_from_state_dict(module, state_dict, prefix, local_metadata,
                                   missing_keys, unexpected_keys, weight_shape,
                                   bias_shape=None):
        assign_to_params_buffers = local_metadata.get("assign_to_params_buffers", False)
        prefix_len = len(prefix)
        for k, v in state_dict.items():
            key = k[prefix_len:]
            if key == "weight":
                if not assign_to_params_buffers:
                    v = v.clone()
                module.weight = torch.nn.Parameter(v, requires_grad=False)
            elif bias_shape is not None and key == "bias" and v is not None:
                if not assign_to_params_buffers:
                    v = v.clone()
                module.bias = torch.nn.Parameter(v, requires_grad=False)
            else:
                unexpected_keys.append(k)

        if module.weight is None:
            module.weight = torch.nn.Parameter(torch.zeros(weight_shape), requires_grad=False)
            missing_keys.append(prefix + "weight")

        if bias_shape is not None and module.bias is None and getattr(module, "comfy_need_lazy_init_bias", False):
            module.bias = torch.nn.Parameter(torch.zeros(bias_shape), requires_grad=False)
            missing_keys.append(prefix + "bias")