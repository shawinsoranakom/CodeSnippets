def _init_weights(self, module):
        """Initialize the weights"""
        factor = self.config.initializer_factor
        if isinstance(module, ChineseCLIPVisionEmbeddings):
            init.normal_(module.class_embedding, mean=0.0, std=module.embed_dim**-0.5 * factor)
            init.normal_(module.patch_embedding.weight, std=module.config.initializer_range * factor)
            init.normal_(module.position_embedding.weight, std=module.config.initializer_range * factor)
            init.copy_(module.position_ids, torch.arange(module.num_positions).expand((1, -1)))
        elif isinstance(module, ChineseCLIPTextEmbeddings):
            init.normal_(module.word_embeddings.weight, mean=0.0, std=self.config.initializer_range)
            init.normal_(module.position_embeddings.weight, mean=0.0, std=self.config.initializer_range)
            init.normal_(module.token_type_embeddings.weight, mean=0.0, std=self.config.initializer_range)
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
            init.zeros_(module.token_type_ids)
            for embedding in [module.word_embeddings, module.position_embeddings, module.token_type_embeddings]:
                if embedding.padding_idx is not None:
                    init.zeros_(embedding.weight[embedding.padding_idx])
        elif isinstance(module, ChineseCLIPVisionAttention):
            in_proj_std = (module.embed_dim**-0.5) * ((2 * module.config.num_hidden_layers) ** -0.5) * factor
            out_proj_std = (module.embed_dim**-0.5) * factor
            init.normal_(module.q_proj.weight, std=in_proj_std)
            init.normal_(module.k_proj.weight, std=in_proj_std)
            init.normal_(module.v_proj.weight, std=in_proj_std)
            init.normal_(module.out_proj.weight, std=out_proj_std)
        elif isinstance(module, ChineseCLIPVisionMLP):
            in_proj_std = (module.config.hidden_size**-0.5) * ((2 * module.config.num_hidden_layers) ** -0.5) * factor
            fc_std = (2 * module.config.hidden_size) ** -0.5 * factor
            init.normal_(module.fc1.weight, std=fc_std)
            init.normal_(module.fc2.weight, std=in_proj_std)
        elif isinstance(module, ChineseCLIPModel):
            init.normal_(
                module.text_projection.weight,
                std=module.text_embed_dim**-0.5 * factor,
            )
            init.normal_(
                module.visual_projection.weight,
                std=module.vision_embed_dim**-0.5 * factor,
            )

        if isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=factor)
            if module.bias is not None:
                init.zeros_(module.bias)