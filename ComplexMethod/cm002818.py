def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, Swinv2Embeddings):
            if module.mask_token is not None:
                init.zeros_(module.mask_token)
            if module.position_embeddings is not None:
                init.zeros_(module.position_embeddings)
        elif isinstance(module, Swinv2SelfAttention):
            init.constant_(module.logit_scale, math.log(10))
            relative_coords_table, relative_position_index = module.create_coords_table_and_index()
            init.copy_(module.relative_coords_table, relative_coords_table)
            init.copy_(module.relative_position_index, relative_position_index)