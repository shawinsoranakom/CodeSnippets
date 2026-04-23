def check_config_arguments_init(self):
        if self.config_class.sub_configs:
            return  # TODO: @raushan composite models are not consistent in how they set general params

        kwargs = copy.deepcopy(config_common_kwargs)
        config = self.config_class(**kwargs)
        wrong_values = []
        for key, value in config_common_kwargs.items():
            if key == "dtype":
                if not is_torch_available():
                    continue
                else:
                    import torch

                    if config.dtype != torch.float16:
                        wrong_values.append(("dtype", config.dtype, torch.float16))
            elif getattr(config, key) != value:
                wrong_values.append((key, getattr(config, key), value))

        if len(wrong_values) > 0:
            errors = "\n".join([f"- {v[0]}: got {v[1]} instead of {v[2]}" for v in wrong_values])
            raise ValueError(f"The following keys were not properly set in the config:\n{errors}")