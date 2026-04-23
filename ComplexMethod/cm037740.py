def _ssm_transform(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # LoRA kernel requires contiguous tensor.
        # ROCm: Non-contiguous tensors cause incorrect GEMM
        # results when batch > 1.
        if self.is_lora_enabled or current_platform.is_rocm():
            x = x.contiguous()
        ssm_params = self.x_proj(x)[0]
        time_step, B, C = torch.split(
            ssm_params,
            [self.time_step_rank, self.ssm_state_size, self.ssm_state_size],
            dim=-1,
        )
        if self.use_rms_norm:
            assert self.dt_layernorm is not None
            assert self.b_layernorm is not None
            assert self.c_layernorm is not None
            time_step = self.dt_layernorm(time_step.contiguous())
            B = self.b_layernorm(B.contiguous())
            C = self.c_layernorm(C.contiguous())

        # ROCm: tensor from split is non-contiguous, causing incorrect
        # GEMM results in dt_proj.
        if current_platform.is_rocm():
            time_step = time_step.contiguous()

        discrete_time_step = self.dt_proj(time_step)[0].transpose(-2, -1)
        return discrete_time_step, B, C