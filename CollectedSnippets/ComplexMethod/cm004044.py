def _init_weights(self, module: nn.Module):
        std = self.config.initializer_factor
        if isinstance(module, BridgeTowerVisionTransformer):
            proj_std = (self.config.hidden_size**-0.5) * ((2 * self.config.num_hidden_layers) ** -0.5)
            attn_std = self.config.hidden_size**-0.5
            fc_std = (2 * self.config.hidden_size) ** -0.5
            for block in module.transformer.resblocks:
                init.normal_(block.attn.in_proj_weight, std=attn_std * std)
                init.zeros_(block.attn.in_proj_bias)
                init.normal_(block.attn.out_proj.weight, std=proj_std * std)
                init.normal_(block.mlp.c_fc.weight, std=fc_std * std)
                init.normal_(block.mlp.c_proj.weight, std=proj_std * std)

            init.normal_(module.embeddings.class_embedding, std=attn_std * std)
            init.normal_(module.embeddings.position_embedding.weight, std=attn_std * std)
        elif isinstance(module, (nn.Linear, nn.Conv2d, nn.Embedding)):
            init.normal_(module.weight, mean=0.0, std=0.05 * std)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, BridgeTowerForContrastiveLearning):
            init.constant_(module.logit_scale, self.config.logit_scale_init_value)
        elif isinstance(module, BridgeTowerVisionEmbeddings):
            init.copy_(module.position_ids, torch.arange(module.num_positions).expand((1, -1)))
        elif isinstance(module, BridgeTowerTextEmbeddings):
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
            init.zeros_(module.token_type_ids)

        if isinstance(module, (nn.Linear, BridgeTowerMLMHead)) and module.bias is not None:
            init.zeros_(module.bias)