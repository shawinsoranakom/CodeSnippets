def _init_weights(self, module: nn.Module):
        """Initialize the weights"""
        std = self.config.initializer_range
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, (nn.Conv1d, nn.ConvTranspose1d)):
            init.kaiming_normal_(module.weight)
            if module.bias is not None:
                k = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                init.uniform_(module.bias, a=-k, b=k)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, VitsAttention):
            if self.config.window_size:
                head_dim = self.config.hidden_size // self.config.num_attention_heads
                init.normal_(module.emb_rel_k, std=head_dim**-0.5)
                init.normal_(module.emb_rel_v, std=head_dim**-0.5)
        elif isinstance(module, VitsElementwiseAffine):
            init.zeros_(module.translate)
            init.zeros_(module.log_scale)