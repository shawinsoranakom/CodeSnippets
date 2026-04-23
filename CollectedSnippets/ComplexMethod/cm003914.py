def _init_weights(self, module):
        """Initialize the weights"""

        init_std = self.config.initializer_range
        if isinstance(module, VJEPA2AttentivePooler):
            init.trunc_normal_(module.query_tokens, std=init_std)
            for i, layer in enumerate(module.self_attention_layers, 1):
                std = init_std / (i**0.5)
                init.trunc_normal_(layer.self_attn.out_proj.weight, std=std)
                init.trunc_normal_(layer.mlp.fc2.weight, std=std)
            std = init_std / (len(module.self_attention_layers) + 1) ** 0.5
            init.trunc_normal_(module.cross_attention_layer.mlp.fc2.weight, std=std)
        elif isinstance(module, VJEPA2PredictorEmbeddings):
            if module.zero_init_mask_tokens:
                init.zeros_(module.mask_tokens)
            else:
                init.trunc_normal_(module.mask_tokens, std=init_std)
        elif isinstance(module, (nn.Linear, nn.Conv2d, nn.Conv3d)):
            init.trunc_normal_(module.weight, std=init_std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)