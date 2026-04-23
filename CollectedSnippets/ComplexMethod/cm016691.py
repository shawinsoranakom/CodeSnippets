def __init__(self, latent_input=False, num_union_modes=0, mistoline=False, control_latent_channels=None, image_model=None, dtype=None, device=None, operations=None, **kwargs):
        super().__init__(final_layer=False, dtype=dtype, device=device, operations=operations, **kwargs)

        self.main_model_double = 19
        self.main_model_single = 38

        self.mistoline = mistoline
        # add ControlNet blocks
        if self.mistoline:
            control_block = lambda : MistolineControlnetBlock(self.hidden_size, dtype=dtype, device=device, operations=operations)
        else:
            control_block = lambda : operations.Linear(self.hidden_size, self.hidden_size, dtype=dtype, device=device)

        self.controlnet_blocks = nn.ModuleList([])
        for _ in range(self.params.depth):
            self.controlnet_blocks.append(control_block())

        self.controlnet_single_blocks = nn.ModuleList([])
        for _ in range(self.params.depth_single_blocks):
            self.controlnet_single_blocks.append(control_block())

        self.num_union_modes = num_union_modes
        self.controlnet_mode_embedder = None
        if self.num_union_modes > 0:
            self.controlnet_mode_embedder = operations.Embedding(self.num_union_modes, self.hidden_size, dtype=dtype, device=device)

        self.gradient_checkpointing = False
        self.latent_input = latent_input
        if control_latent_channels is None:
            control_latent_channels = self.in_channels
        else:
            control_latent_channels *= 2 * 2 #patch size

        self.pos_embed_input = operations.Linear(control_latent_channels, self.hidden_size, bias=True, dtype=dtype, device=device)
        if not self.latent_input:
            if self.mistoline:
                self.input_cond_block = MistolineCondDownsamplBlock(dtype=dtype, device=device, operations=operations)
            else:
                self.input_hint_block = nn.Sequential(
                    operations.Conv2d(3, 16, 3, padding=1, dtype=dtype, device=device),
                    nn.SiLU(),
                    operations.Conv2d(16, 16, 3, padding=1, dtype=dtype, device=device),
                    nn.SiLU(),
                    operations.Conv2d(16, 16, 3, padding=1, stride=2, dtype=dtype, device=device),
                    nn.SiLU(),
                    operations.Conv2d(16, 16, 3, padding=1, dtype=dtype, device=device),
                    nn.SiLU(),
                    operations.Conv2d(16, 16, 3, padding=1, stride=2, dtype=dtype, device=device),
                    nn.SiLU(),
                    operations.Conv2d(16, 16, 3, padding=1, dtype=dtype, device=device),
                    nn.SiLU(),
                    operations.Conv2d(16, 16, 3, padding=1, stride=2, dtype=dtype, device=device),
                    nn.SiLU(),
                    operations.Conv2d(16, 16, 3, padding=1, dtype=dtype, device=device)
                )