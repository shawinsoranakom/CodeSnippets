def state_dict_for_saving(self, clip_state_dict=None, vae_state_dict=None, clip_vision_state_dict=None):
        unet_state_dict = self.model.diffusion_model.state_dict()
        for k, v in unet_state_dict.items():
            op_keys = k.rsplit('.', 1)
            if (len(op_keys) < 2) or op_keys[1] not in ["weight", "bias"]:
                continue
            try:
                op = comfy.utils.get_attr(self.model.diffusion_model, op_keys[0])
            except:
                continue
            if not op or not hasattr(op, "comfy_cast_weights") or \
                (hasattr(op, "comfy_patched_weights") and op.comfy_patched_weights == True):
                continue
            key = "diffusion_model." + k
            unet_state_dict[k] = LazyCastingParam(self, key, comfy.utils.get_attr(self.model, key))
        return self.model.state_dict_for_saving(unet_state_dict, clip_state_dict=clip_state_dict, vae_state_dict=vae_state_dict, clip_vision_state_dict=clip_vision_state_dict)