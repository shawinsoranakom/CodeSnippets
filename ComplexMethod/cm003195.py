def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, Wav2Vec2BertSelfAttention):
            if hasattr(module, "pos_bias_u"):
                init.xavier_uniform_(module.pos_bias_u)
            if hasattr(module, "pos_bias_v"):
                init.xavier_uniform_(module.pos_bias_v)
        elif isinstance(module, Wav2Vec2BertFeatureProjection):
            k = math.sqrt(1 / module.projection.in_features)
            init.uniform_(module.projection.weight, a=-k, b=k)
            init.uniform_(module.projection.bias, a=-k, b=k)
        elif isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)

            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, nn.Conv1d):
            init.kaiming_normal_(module.weight)

            if module.bias is not None:
                k = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                init.uniform_(module.bias, a=-k, b=k)
        elif isinstance(module, Wav2Vec2BertModel):
            if hasattr(module, "masked_spec_embed"):
                init.uniform_(module.masked_spec_embed)
        elif isinstance(
            module,
            (Wav2Vec2BertForSequenceClassification, Wav2Vec2BertForAudioFrameClassification, Wav2Vec2BertForXVector),
        ):
            if hasattr(module, "layer_weights"):
                init.constant_(module.layer_weights, 1.0 / (self.config.num_hidden_layers + 1))
        elif isinstance(module, AMSoftmaxLoss):  # noqa: F821
            init.normal_(module.weight)
        elif isinstance(module, Wav2Vec2BertRotaryPositionalEmbedding):
            dim = self.config.hidden_size // self.config.num_attention_heads
            base = self.config.rotary_embedding_base
            inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2, dtype=torch.int64).float() / dim))
            init.copy_(module.inv_freq, inv_freq)
        elif isinstance(module, Wav2Vec2BertRelPositionalEmbedding):
            init.copy_(module.pe, module.extend_pe(torch.tensor(0.0).expand(1, module.max_len)))