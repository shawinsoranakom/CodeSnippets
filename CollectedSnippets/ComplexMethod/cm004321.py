def _init_weights(self, module):
        std = math.sqrt(self.config.w_init_variance_scale / self.config.conv1d_width)
        if isinstance(module, nn.Conv1d):
            init.normal_(module.weight, mean=0.0, std=std)
            init.zeros_(module.bias)
        elif isinstance(module, RecurrentGemmaSdpaAttention):
            init.normal_(module.q_proj.weight, mean=0.0, std=math.sqrt(1.0 / self.config.hidden_size))
            init.normal_(module.k_proj.weight, mean=0.0, std=math.sqrt(1.0 / self.config.hidden_size))
            init.normal_(module.v_proj.weight, mean=0.0, std=math.sqrt(1.0 / self.config.hidden_size))

            std = math.sqrt(self.config.final_w_init_variance_scale / self.config.hidden_size)
            init.normal_(module.o_proj.weight, mean=0.0, std=std)
        elif isinstance(module, RecurrentGemmaRecurrentBlock):
            init.zeros_(module.linear_x.bias)
            init.normal_(module.linear_x.weight, mean=0.0, std=math.sqrt(1.0 / self.config.hidden_size))

            init.zeros_(module.linear_y.bias)
            init.normal_(module.linear_y.weight, mean=0.0, std=math.sqrt(1.0 / self.config.hidden_size))

            std = math.sqrt(self.config.final_w_init_variance_scale / self.config.lru_width)
            init.normal_(module.linear_out.weight, mean=0.0, std=std)
            init.zeros_(module.linear_out.bias)
        elif isinstance(module, RecurrentGemmaRglru):
            std = math.sqrt(
                self.config.w_init_variance_scale / (self.config.lru_width // self.config.num_attention_heads)
            )
            init.normal_(module.input_gate_weight, mean=0.0, std=std)
            init.normal_(module.recurrent_gate_weight, mean=0.0, std=std)
            init.zeros_(module.input_gate_bias)
            init.zeros_(module.recurrent_gate_bias)

            recurrent_param = torch.empty_like(module.recurrent_param).uniform_(0.9**2 + 1e-8, 0.999**2 + 1e-8)
            recurrent_param.log_().mul_(0.5).neg_().exp_().sub_(1.0).log_()
            init.copy_(module.recurrent_param, recurrent_param)
        elif isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=std)
            if getattr(module, "bias", None) is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        # We initialize with 0s to be 1 centered as the RMSNorm here does (1 + weight)
        elif isinstance(module, RecurrentGemmaRMSNorm):
            init.zeros_(module.weight)
        elif isinstance(module, RecurrentGemmaModel):
            init.constant_(module.normalizer, module.config.hidden_size**0.5)
        elif isinstance(module, RecurrentGemmaRotaryEmbedding):
            buffer_value, _ = module.compute_default_rope_parameters(module.config)
            init.copy_(module.inv_freq, buffer_value)
            init.copy_(module.original_inv_freq, buffer_value)