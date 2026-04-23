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
        elif isinstance(module, SeamlessM4Tv2ConformerSelfAttention):
            if hasattr(module, "pos_bias_u"):
                init.xavier_uniform_(module.pos_bias_u)
            if hasattr(module, "pos_bias_v"):
                init.xavier_uniform_(module.pos_bias_v)
        elif isinstance(module, SeamlessM4Tv2ConformerFeatureProjection):
            k = math.sqrt(1 / module.projection.in_features)
            init.uniform_(module.projection.weight, a=-k, b=k)
            init.uniform_(module.projection.bias, a=-k, b=k)
        elif isinstance(module, SeamlessM4Tv2TextToUnitDecoder):
            init.ones_(module.pos_emb_alpha_char)
            init.ones_(module.pos_emb_alpha)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, (nn.Conv1d, nn.ConvTranspose1d)):
            init.kaiming_normal_(module.weight)
            if module.bias is not None:
                k = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                init.uniform_(module.bias, a=-k, b=k)
        elif isinstance(module, SeamlessM4Tv2SinusoidalPositionalEmbedding):
            emb_weights = module.get_embedding(
                module.num_positions + module.offset, module.embedding_dim, module.padding_idx
            )
            init.copy_(module.weights, emb_weights)