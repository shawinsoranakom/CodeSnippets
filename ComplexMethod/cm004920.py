def _init_weights(self, module):
        """Initialize the weights."""
        super()._init_weights(module)
        if isinstance(module, NemotronHMamba2Mixer):
            # Initialize A_log and D parameters
            A = torch.arange(1, self.config.mamba_num_heads + 1)
            init.copy_(module.A_log, torch.log(A))
            init.ones_(module.D)

            dt = torch.exp(
                torch.rand(self.config.mamba_num_heads)
                * (math.log(self.config.time_step_max) - math.log(self.config.time_step_min))
                + math.log(self.config.time_step_min)
            ).clamp(min=self.config.time_step_floor)

            # # Inverse of softplus: https://github.com/pytorch/pytorch/issues/72759
            inv_dt = dt + torch.log(-torch.expm1(-dt))
            with torch.no_grad():
                init.copy_(module.dt_bias, inv_dt)
            module.dt_bias._no_reinit = True
        elif isinstance(module, NemotronHTopkRouter):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            init.zeros_(module.e_score_correction_bias)
        elif isinstance(module, NemotronHExperts):
            # Initialize expert weights
            init.normal_(module.up_proj, mean=0.0, std=self.config.initializer_range)
            init.normal_(module.down_proj, mean=0.0, std=self.config.initializer_range)

        if isinstance(module, nn.Linear):
            if module.bias is not None:
                if not getattr(module.bias, "_no_reinit", False):
                    init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, std=self.config.initializer_range)

        if self.config.rescale_prenorm_residual:
            # Reinitialize selected weights subject to the OpenAI GPT-2 Paper Scheme:
            #   > A modified initialization which accounts for the accumulation on the residual path with model depth. Scale
            #   > the weights of residual layers at initialization by a factor of 1/√N where N is the # of residual layers.
            #   >   -- GPT-2 :: https://openai.com/blog/better-language-models/
            #
            # Reference (Megatron-LM): https://github.com/NVIDIA/Megatron-LM/blob/main/megatron/model/gpt_model.py
            for name, p in module.named_parameters():
                if name == "out_proj.weight":
                    # Special Scaled Initialization --> There are 2 Layer Norms per Transformer Block
                    # Following Pytorch init, except scale by 1/sqrt(2 * n_layer)
                    # We need to reinit p since this code could be called multiple times
                    # Having just p *= scale would repeatedly scale it down
                    init.kaiming_uniform_(p, a=math.sqrt(5))
                    with torch.no_grad():
                        p_new = p / math.sqrt(self.config.num_hidden_layers)
                        init.copy_(p, p_new)