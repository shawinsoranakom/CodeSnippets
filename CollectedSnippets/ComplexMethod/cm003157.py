def _init_weights(self, module: nn.Module):
        """Initialize the weights"""
        std = self.config.initializer_range
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, SeamlessM4TConformerSelfAttention):
            if hasattr(module, "pos_bias_u"):
                init.xavier_uniform_(module.pos_bias_u)
            if hasattr(module, "pos_bias_v"):
                init.xavier_uniform_(module.pos_bias_v)
        elif isinstance(module, SeamlessM4TConformerPositionalConvEmbedding):
            init.normal_(
                module.conv.weight,
                mean=0,
                std=2 * math.sqrt(1 / (module.conv.kernel_size[0] * module.conv.in_channels)),
            )
            init.constant_(module.conv.bias, 0)
        elif isinstance(module, SeamlessM4TConformerFeatureProjection):
            k = math.sqrt(1 / module.projection.in_features)
            init.uniform_(module.projection.weight, a=-k, b=k)
            init.uniform_(module.projection.bias, a=-k, b=k)
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm1d)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, nn.Conv1d):
            init.kaiming_normal_(module.weight)
            if module.bias is not None:
                k = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                init.uniform_(module.bias, a=-k, b=k)
        elif isinstance(module, SeamlessM4TSinusoidalPositionalEmbedding):
            emb_weights = module.get_embedding(
                module.num_positions + module.offset, module.embedding_dim, module.padding_idx
            )
            init.copy_(module.weights, emb_weights)
        elif isinstance(module, SeamlessM4TConformerRotaryPositionalEmbedding):
            dim = self.config.hidden_size // self.config.speech_encoder_attention_heads
            base = self.config.rotary_embedding_base
            inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2, dtype=torch.int64).float() / dim))
            init.copy_(module.inv_freq, inv_freq)
        elif isinstance(module, SeamlessM4TConformerRelPositionalEmbedding):
            init.copy_(module.pe, module.extend_pe(torch.tensor(0.0).expand(1, module.max_len)))