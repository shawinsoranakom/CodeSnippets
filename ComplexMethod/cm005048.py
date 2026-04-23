def _init_weights(self, module):
        """Initialize the weights"""
        super()._init_weights(module)

        # Initialize positional embeddings to zero (SLANeXtVisionEncoder holds pos_embed)
        if isinstance(module, SLANeXtVisionEncoder):
            if module.pos_embed is not None:
                init.constant_(module.pos_embed, 0.0)

        # Initialize relative positional embeddings to zero (SLANeXtVisionAttention holds rel_pos_h/w)
        if isinstance(module, SLANeXtVisionAttention):
            if module.use_rel_pos:
                init.constant_(module.rel_pos_h, 0.0)
                init.constant_(module.rel_pos_w, 0.0)

        # Initialize GRUCell (replicates PyTorch default reset_parameters)
        if isinstance(module, nn.GRUCell):
            std = 1.0 / math.sqrt(module.hidden_size) if module.hidden_size > 0 else 0
            init.uniform_(module.weight_ih, -std, std)
            init.uniform_(module.weight_hh, -std, std)
            if module.bias_ih is not None:
                init.uniform_(module.bias_ih, -std, std)
            if module.bias_hh is not None:
                init.uniform_(module.bias_hh, -std, std)

        # Initialize SLAHead layers
        if isinstance(module, SLANeXtSLAHead):
            std = 1.0 / math.sqrt(self.config.hidden_size * 1.0)
            # Initialize structure_generator and loc_generator layers
            for generator in (module.structure_generator,):
                for layer in generator.children():
                    if isinstance(layer, nn.Linear):
                        init.uniform_(layer.weight, -std, std)
                        if layer.bias is not None:
                            init.uniform_(layer.bias, -std, std)