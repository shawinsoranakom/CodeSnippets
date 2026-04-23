def pre_run(self, model, percent_to_timestep_function):
        super().pre_run(model, percent_to_timestep_function)
        controlnet_config = model.model_config.unet_config.copy()
        controlnet_config.pop("out_channels")
        controlnet_config["hint_channels"] = self.control_weights["input_hint_block.0.weight"].shape[1]
        self.manual_cast_dtype = model.manual_cast_dtype
        dtype = model.get_dtype()
        if self.manual_cast_dtype is None:
            class control_lora_ops(ControlLoraOps, comfy.ops.disable_weight_init):
                pass
        else:
            class control_lora_ops(ControlLoraOps, comfy.ops.manual_cast):
                pass
            dtype = self.manual_cast_dtype

        controlnet_config["operations"] = control_lora_ops
        controlnet_config["dtype"] = dtype
        self.control_model = comfy.cldm.cldm.ControlNet(**controlnet_config)
        self.control_model.to(comfy.model_management.get_torch_device())
        diffusion_model = model.diffusion_model
        sd = diffusion_model.state_dict()

        for k in sd:
            weight = sd[k]
            try:
                comfy.utils.set_attr_param(self.control_model, k, weight)
            except:
                pass

        for k in self.control_weights:
            if (k not in {"lora_controlnet"}):
                if (k.endswith(".up") or k.endswith(".down") or k.endswith(".weight") or k.endswith(".bias")) and ("__" not in k):
                    comfy.utils.set_attr_param(self.control_model, k, self.control_weights[k].to(dtype).to(comfy.model_management.get_torch_device()))