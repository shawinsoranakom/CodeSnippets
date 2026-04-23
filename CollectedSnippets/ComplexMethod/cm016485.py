def get_control(self, x_noisy, t, cond, batched_number, transformer_options):
        control_prev = None
        if self.previous_controlnet is not None:
            control_prev = self.previous_controlnet.get_control(x_noisy, t, cond, batched_number, transformer_options)

        if self.timestep_range is not None:
            if t[0] > self.timestep_range[0] or t[0] < self.timestep_range[1]:
                if control_prev is not None:
                    return control_prev
                else:
                    return None

        if self.cond_hint is None or x_noisy.shape[2] * self.compression_ratio != self.cond_hint.shape[2] or x_noisy.shape[3] * self.compression_ratio != self.cond_hint.shape[3]:
            if self.cond_hint is not None:
                del self.cond_hint
            self.control_input = None
            self.cond_hint = None
            width, height = self.scale_image_to(x_noisy.shape[3] * self.compression_ratio, x_noisy.shape[2] * self.compression_ratio)
            self.cond_hint = comfy.utils.common_upscale(self.cond_hint_original, width, height, self.upscale_algorithm, "center").float().to(self.device)
            if self.channels_in == 1 and self.cond_hint.shape[1] > 1:
                self.cond_hint = torch.mean(self.cond_hint, 1, keepdim=True)
        if x_noisy.shape[0] != self.cond_hint.shape[0]:
            self.cond_hint = broadcast_image_to(self.cond_hint, x_noisy.shape[0], batched_number)
        if self.control_input is None:
            self.t2i_model.to(x_noisy.dtype)
            self.t2i_model.to(self.device)
            self.control_input = self.t2i_model(self.cond_hint.to(x_noisy.dtype))
            self.t2i_model.cpu()

        control_input = {}
        for k in self.control_input:
            control_input[k] = list(map(lambda a: None if a is None else a.clone(), self.control_input[k]))

        return self.control_merge(control_input, control_prev, x_noisy.dtype)