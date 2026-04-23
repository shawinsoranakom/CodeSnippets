def _init_weights(self, module):
        """Initialize the weights"""
        PreTrainedModel._init_weights(module)

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
        if isinstance(module, SLANetSLAHead):
            std = 1.0 / math.sqrt(self.config.hidden_size * 1.0)
            # Initialize structure_generator and loc_generator layers
            for generator in (module.structure_generator,):
                for layer in generator.children():
                    if isinstance(layer, nn.Linear):
                        init.uniform_(layer.weight, -std, std)
                        if layer.bias is not None:
                            init.uniform_(layer.bias, -std, std)