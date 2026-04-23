def cuda_kernels_forward(
        self,
        hidden_states: torch.Tensor,
        cache_params: Cache | None = None,
        attention_mask: torch.LongTensor | None = None,
    ):
        # 1. Gated MLP's linear projection
        projected_states = self.in_proj(hidden_states).transpose(1, 2)
        if self.training and cache_params is None:  # Doesn't support outputting the states -> used for training
            contextualized_states = falcon_mamba_inner_fn(
                projected_states,
                self.conv1d.weight,
                self.conv1d.bias if self.use_conv_bias else None,
                self.x_proj.weight,
                self.dt_proj.weight,
                self.out_proj.weight,
                self.out_proj.bias.float() if self.use_bias else None,
                -torch.exp(self.A_log.float()),
                None,  # input-dependent B
                None,  # input-dependent C
                self.D.float(),
                delta_bias=self.dt_proj.bias.float(),
                delta_softplus=True,
                b_rms_weight=self.b_c_rms,
                c_rms_weight=self.b_c_rms,
                dt_rms_weight=self.dt_rms,
                b_c_dt_rms_eps=self.rms_eps,
            )

        else:
            hidden_states, gate = projected_states.chunk(2, dim=1)

            if attention_mask is not None:
                hidden_states = hidden_states * attention_mask.unsqueeze(1)

            is_decoding = cache_params is not None and cache_params.has_previous_state(self.layer_idx)

            # 2. Convolution sequence transformation
            conv_weights = self.conv1d.weight.view(self.conv1d.weight.size(0), self.conv1d.weight.size(2))
            if is_decoding:
                hidden_states = causal_conv1d_update(
                    hidden_states.squeeze(-1),
                    cache_params.layers[self.layer_idx].conv_states,
                    conv_weights,
                    self.conv1d.bias,
                    self.activation,
                )
                hidden_states = hidden_states.unsqueeze(-1)
            else:
                if cache_params is not None:
                    conv_states = nn.functional.pad(
                        hidden_states, (self.conv_kernel_size - hidden_states.shape[-1], 0)
                    )
                    cache_params.update_conv_state(conv_states, self.layer_idx)
                hidden_states = causal_conv1d_fn(
                    hidden_states, conv_weights, self.conv1d.bias, activation=self.activation
                )

            if attention_mask is not None:
                hidden_states = hidden_states * attention_mask.unsqueeze(1)

            # 3. State Space Model sequence transformation
            # 3.a. input varying initialization of time_step, B and C
            ssm_parameters = self.x_proj(hidden_states.transpose(1, 2))
            time_step, B, C = torch.split(
                ssm_parameters, [self.time_step_rank, self.ssm_state_size, self.ssm_state_size], dim=-1
            )

            B = rms_forward(B, variance_epsilon=self.rms_eps)
            C = rms_forward(C, variance_epsilon=self.rms_eps)
            time_step = rms_forward(time_step, variance_epsilon=self.rms_eps)

            # In case the model has been quantized, we need a hack to properly call the `nn.Linear` module
            # at the price of a small overhead.
            if hasattr(self.config, "_is_quantized"):
                discrete_time_step = (self.dt_proj(time_step) - self.dt_proj.bias).transpose(1, 2)
            else:
                discrete_time_step = self.dt_proj.weight @ time_step.transpose(1, 2)

            A = -torch.exp(self.A_log.float())
            # 3.c perform the recurrence y ← SSM(A, B, C)(x)
            time_proj_bias = self.dt_proj.bias.float() if hasattr(self.dt_proj, "bias") else None
            if is_decoding:
                scan_outputs = selective_state_update(
                    cache_params.layers[self.layer_idx].recurrent_states,
                    hidden_states[..., 0],
                    discrete_time_step[..., 0],
                    A,
                    B[:, 0],
                    C[:, 0],
                    self.D,
                    gate[..., 0],
                    time_proj_bias,
                    dt_softplus=True,
                ).unsqueeze(-1)
            else:
                scan_outputs, ssm_state = selective_scan_fn(
                    hidden_states,
                    discrete_time_step,
                    A,
                    B.transpose(1, 2),
                    C.transpose(1, 2),
                    self.D.float(),
                    gate,
                    time_proj_bias,
                    delta_softplus=True,
                    return_last_state=True,
                )
                if ssm_state is not None and cache_params is not None:
                    cache_params.update_recurrent_state(ssm_state, self.layer_idx)

            # 4. Final linear projection
            contextualized_states = self.out_proj(scan_outputs.transpose(1, 2))
        return contextualized_states