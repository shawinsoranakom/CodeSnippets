def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, Phi4MultimodalVisionEmbeddings):
            width = (
                self.config.hidden_size
                if isinstance(self.config, Phi4MultimodalVisionConfig)
                else self.config.hidden_size
            )
            init.normal_(module.position_embedding.weight, std=1 / np.sqrt(width))
        elif isinstance(module, nn.Embedding):
            init.default_flax_embed_init_(module.weight)
        elif isinstance(module, Phi4MultimodalVisionAttention):
            init.normal_(module.q_proj.weight)
            init.normal_(module.k_proj.weight)
            init.normal_(module.v_proj.weight)
            init.normal_(module.out_proj.weight)
            init.zeros_(module.q_proj.bias)
            init.zeros_(module.k_proj.bias)
            init.zeros_(module.v_proj.bias)
            init.zeros_(module.out_proj.bias)
        elif isinstance(module, Phi4MultimodalVisionMLP):
            init.normal_(module.fc1.weight)
            init.normal_(module.fc2.weight)
            init.normal_(module.fc1.bias, std=1e-6)
            init.normal_(module.fc2.bias, std=1e-6)
        elif isinstance(module, Phi4MultimodalVisionMultiheadAttentionPoolingHead):
            init.normal_(module.probe)
            init.normal_(module.attention.in_proj_weight)
            init.zeros_(module.attention.in_proj_bias)
        elif isinstance(module, (nn.Linear, nn.Conv2d)):
            init.lecun_normal_(module.weight)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)