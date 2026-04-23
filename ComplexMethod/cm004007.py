def _init_weights(self, module):
        """Initialize the weights"""
        # Wav2Vec2ForPreTraining last 2 linear layers need standard Linear init.
        if isinstance(module, Wav2Vec2ConformerForPreTraining):
            module.project_hid.reset_parameters()
            module.project_q.reset_parameters()
        # gumbel softmax requires special init
        elif isinstance(module, Wav2Vec2ConformerGumbelVectorQuantizer):
            init.normal_(module.weight_proj.weight, mean=0.0, std=1)
            init.zeros_(module.weight_proj.bias)
            init.uniform_(module.codevectors)
        elif isinstance(module, Wav2Vec2ConformerSelfAttention):
            if hasattr(module, "pos_bias_u"):
                init.xavier_uniform_(module.pos_bias_u)
            if hasattr(module, "pos_bias_v"):
                init.xavier_uniform_(module.pos_bias_v)
        elif isinstance(module, Wav2Vec2ConformerPositionalConvEmbedding):
            init.normal_(
                module.conv.weight,
                mean=0,
                std=2 * math.sqrt(1 / (module.conv.kernel_size[0] * module.conv.in_channels)),
            )
            init.constant_(module.conv.bias, 0)
        elif isinstance(module, Wav2Vec2ConformerFeatureProjection):
            k = math.sqrt(1 / module.projection.in_features)
            init.uniform_(module.projection.weight, a=-k, b=k)
            init.uniform_(module.projection.bias, a=-k, b=k)
        elif isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)

            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm, nn.BatchNorm1d)):
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
        elif isinstance(module, Wav2Vec2ConformerRotaryPositionalEmbedding):
            dim = self.config.hidden_size // self.config.num_attention_heads
            base = self.config.rotary_embedding_base
            inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2, dtype=torch.int64).float() / dim))
            init.copy_(module.inv_freq, inv_freq)
        elif isinstance(module, Wav2Vec2ConformerRelPositionalEmbedding):
            init.copy_(module.pe, module.extend_pe(torch.tensor(0.0).expand(1, module.max_len)))