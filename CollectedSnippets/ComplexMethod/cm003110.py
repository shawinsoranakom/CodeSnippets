def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, Siglip2VisionEmbeddings):
            width = (
                self.config.vision_config.hidden_size
                if isinstance(self.config, Siglip2Config)
                else self.config.hidden_size
            )
            init.normal_(module.position_embedding.weight, std=1 / np.sqrt(width))
            if hasattr(module, "position_ids"):
                init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        elif isinstance(module, nn.Embedding):
            init.default_flax_embed_init_(module.weight)
        elif isinstance(module, Siglip2Attention):
            init.xavier_uniform_(module.q_proj.weight)
            init.xavier_uniform_(module.k_proj.weight)
            init.xavier_uniform_(module.v_proj.weight)
            init.xavier_uniform_(module.out_proj.weight)
            init.zeros_(module.q_proj.bias)
            init.zeros_(module.k_proj.bias)
            init.zeros_(module.v_proj.bias)
            init.zeros_(module.out_proj.bias)
        elif isinstance(module, Siglip2MLP):
            init.xavier_uniform_(module.fc1.weight)
            init.xavier_uniform_(module.fc2.weight)
            init.normal_(module.fc1.bias, std=1e-6)
            init.normal_(module.fc2.bias, std=1e-6)
        elif isinstance(module, Siglip2MultiheadAttentionPoolingHead):
            init.xavier_uniform_(module.probe)
            init.xavier_uniform_(module.attention.in_proj_weight)
            init.zeros_(module.attention.in_proj_bias)
        elif isinstance(module, Siglip2Model):
            init.zeros_(module.logit_scale)
            init.zeros_(module.logit_bias)
        elif isinstance(module, Siglip2ForImageClassification):
            init.normal_(
                module.classifier.weight,
                std=self.config.vision_config.hidden_size**-0.5 * self.config.initializer_factor,
            )
        elif isinstance(module, (nn.Linear, nn.Conv2d)):
            init.lecun_normal_(module.weight)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, Siglip2TextEmbeddings):
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))