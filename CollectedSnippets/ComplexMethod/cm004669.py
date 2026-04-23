def _init_weights(self, module):
        """Initialize the weights."""
        std = self.config.initializer_range
        if isinstance(module, Mamba2Mixer):
            # S4D real initialization. These are not discretized!
            # The core is to load them, compute the discrete states, then write the updated state. Keeps the memory bounded
            module.init_mamba2_weights()

            init.kaiming_uniform_(module.conv1d.weight, a=math.sqrt(5))
            if module.conv1d.bias is not None:
                init.zeros_(module.conv1d.bias)
            init.kaiming_uniform_(module.out_proj.weight, a=math.sqrt(5))

            if self.config.rescale_prenorm_residual:
                # Reinitialize selected weights subject to the OpenAI GPT-2 Paper Scheme:
                #   > A modified initialization which accounts for the accumulation on the residual path with model depth. Scale
                #   > the weights of residual layers at initialization by a factor of 1/√N where N is the # of residual layers.
                #   >   -- GPT-2 :: https://openai.com/blog/better-language-models/
                #
                # Reference (Megatron-LM): https://github.com/NVIDIA/Megatron-LM/blob/main/megatron/model/gpt_model.py
                # Special Scaled Initialization --> There are 2 Layer Norms per Transformer Block
                # Following Pytorch init, except scale by 1/sqrt(2 * n_layer)
                # We need to reinit p since this code could be called multiple times
                # Having just p *= scale would repeatedly scale it down
                p = module.out_proj.weight
                p /= math.sqrt(self.config.num_hidden_layers)

        if isinstance(module, nn.Linear):
            init.normal_(module.weight, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, (Mamba2RMSNorm, MambaRMSNormGated)):
            init.ones_(module.weight)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, std=std)