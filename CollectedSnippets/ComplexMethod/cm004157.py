def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            init.trunc_normal_(module.weight, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, Swin2SRSelfAttention):
            init.constant_(module.logit_scale, math.log(10))
            relative_coords_table, relative_position_index = module.create_coords_table_and_index()
            init.copy_(module.relative_coords_table, relative_coords_table)
            init.copy_(module.relative_position_index, relative_position_index)
        elif isinstance(module, Swin2SRModel):
            if module.config.num_channels == 3 and module.config.num_channels_out == 3:
                mean = torch.tensor([0.4488, 0.4371, 0.4040]).view(1, 3, 1, 1)
            else:
                mean = torch.zeros(1, 1, 1, 1)
            init.copy_(module.mean, mean)