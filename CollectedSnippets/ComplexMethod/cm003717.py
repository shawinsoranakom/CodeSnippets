def _init_weights(self, module: nn.Module):
        """Initialize the weights"""
        factor = self.config.initializer_factor
        if isinstance(module, OwlViTTextEmbeddings):
            init.normal_(module.token_embedding.weight, mean=0.0, std=factor * 0.02)
            init.normal_(module.position_embedding.weight, mean=0.0, std=factor * 0.02)
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        elif isinstance(module, OwlViTVisionEmbeddings):
            init.normal_(module.class_embedding, mean=0.0, std=module.embed_dim**-0.5 * factor)
            init.normal_(module.patch_embedding.weight, std=module.config.initializer_range * factor)
            init.normal_(module.position_embedding.weight, std=module.config.initializer_range * factor)
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        elif isinstance(module, OwlViTAttention):
            in_proj_std = (module.embed_dim**-0.5) * ((2 * module.config.num_hidden_layers) ** -0.5) * factor
            out_proj_std = (module.embed_dim**-0.5) * factor
            init.normal_(module.q_proj.weight, std=in_proj_std)
            init.normal_(module.k_proj.weight, std=in_proj_std)
            init.normal_(module.v_proj.weight, std=in_proj_std)
            init.normal_(module.out_proj.weight, std=out_proj_std)
        elif isinstance(module, OwlViTMLP):
            in_proj_std = (module.config.hidden_size**-0.5) * ((2 * module.config.num_hidden_layers) ** -0.5) * factor
            fc_std = (2 * module.config.hidden_size) ** -0.5 * factor
            init.normal_(module.fc1.weight, std=fc_std)
            init.normal_(module.fc2.weight, std=in_proj_std)
        elif isinstance(module, OwlViTModel):
            init.normal_(
                module.text_projection.weight,
                std=module.text_embed_dim**-0.5 * factor,
            )
            init.normal_(
                module.visual_projection.weight,
                std=module.vision_embed_dim**-0.5 * factor,
            )
            init.constant_(module.logit_scale, self.config.logit_scale_init_value)
        elif isinstance(module, OwlViTForObjectDetection):
            init.copy_(module.box_bias, module.compute_box_bias(module.num_patches_height, module.num_patches_width))
        if isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=factor)
            if module.bias is not None:
                init.zeros_(module.bias)