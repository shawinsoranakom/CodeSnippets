def _init_weights(self, module: nn.Module):
        """Initialize the weights"""
        if hasattr(self.config, "initializer_factor"):
            factor = self.config.initializer_factor
        elif hasattr(self.config, "vision_config"):
            factor = self.config.vision_config.initializer_factor

        if hasattr(self.config, "init_std"):
            std = self.config.init_std
        elif hasattr(self.config, "text_config"):
            std = self.config.text_config.init_std

        if isinstance(module, Kosmos2VisionEmbeddings):
            init.normal_(module.class_embedding, mean=0.0, std=module.embed_dim**-0.5 * factor)
            init.normal_(module.patch_embedding.weight, std=module.config.initializer_range * factor)
            init.normal_(module.position_embedding.weight, std=module.config.initializer_range * factor)
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        elif isinstance(module, Kosmos2VisionAttention):
            in_proj_std = (module.embed_dim**-0.5) * ((2 * module.config.num_hidden_layers) ** -0.5) * factor
            out_proj_std = (module.embed_dim**-0.5) * factor
            init.normal_(module.q_proj.weight, std=in_proj_std)
            init.normal_(module.k_proj.weight, std=in_proj_std)
            init.normal_(module.v_proj.weight, std=in_proj_std)
            init.normal_(module.out_proj.weight, std=out_proj_std)
        elif isinstance(module, Kosmos2VisionMLP):
            in_proj_std = (module.config.hidden_size**-0.5) * ((2 * module.config.num_hidden_layers) ** -0.5) * factor
            fc_std = (2 * module.config.hidden_size) ** -0.5 * factor
            init.normal_(module.fc1.weight, std=fc_std)
            init.normal_(module.fc2.weight, std=in_proj_std)
        elif isinstance(module, KosmosTextAttention):
            init.normal_(module.q_proj.weight, std=std)
            init.normal_(module.k_proj.weight, std=std)
            init.normal_(module.v_proj.weight, std=std)
            init.normal_(module.out_proj.weight, std=std)
        elif isinstance(module, Kosmos2TextFFN):
            init.normal_(module.fc1.weight, std=std)
            init.normal_(module.fc2.weight, std=std)
        elif isinstance(module, Kosmos2TextForCausalLM):
            init.normal_(module.lm_head.weight, std=std)
        elif isinstance(module, Kosmos2ImageToTextProjection):
            init.normal_(module.dense.weight, std=std)
            init.normal_(module.latent_query)
        elif isinstance(module, Kosmos2TextTransformer):
            init.normal_(module.embed_tokens.weight, mean=0.0, std=std)
            if module.embed_tokens.padding_idx is not None:
                init.zeros_(module.embed_tokens.weight[module.embed_tokens.padding_idx])
        elif isinstance(module, nn.LayerNorm):
            init.ones_(module.weight)
            init.zeros_(module.bias)
        elif isinstance(module, Kosmos2TextSinusoidalPositionalEmbedding):
            emb_weights = module.get_embedding(
                module.num_positions + module.offset, module.embedding_dim, module.padding_idx
            )
            init.copy_(module.weights, emb_weights)

        if isinstance(module, nn.Linear) and module.bias is not None:
            init.zeros_(module.bias)