def __init__(self,
        io_channels=64,
        patch_size=1,
        embed_dim=1536,
        cond_token_dim=768,
        project_cond_tokens=False,
        global_cond_dim=1536,
        project_global_cond=True,
        input_concat_dim=0,
        prepend_cond_dim=0,
        depth=24,
        num_heads=24,
        transformer_type: tp.Literal["continuous_transformer"] = "continuous_transformer",
        global_cond_type: tp.Literal["prepend", "adaLN"] = "prepend",
        audio_model="",
        dtype=None,
        device=None,
        operations=None,
        **kwargs):

        super().__init__()

        self.dtype = dtype
        self.cond_token_dim = cond_token_dim

        # Timestep embeddings
        timestep_features_dim = 256

        self.timestep_features = FourierFeatures(1, timestep_features_dim, dtype=dtype, device=device)

        self.to_timestep_embed = nn.Sequential(
            operations.Linear(timestep_features_dim, embed_dim, bias=True, dtype=dtype, device=device),
            nn.SiLU(),
            operations.Linear(embed_dim, embed_dim, bias=True, dtype=dtype, device=device),
        )

        if cond_token_dim > 0:
            # Conditioning tokens

            cond_embed_dim = cond_token_dim if not project_cond_tokens else embed_dim
            self.to_cond_embed = nn.Sequential(
                operations.Linear(cond_token_dim, cond_embed_dim, bias=False, dtype=dtype, device=device),
                nn.SiLU(),
                operations.Linear(cond_embed_dim, cond_embed_dim, bias=False, dtype=dtype, device=device)
            )
        else:
            cond_embed_dim = 0

        if global_cond_dim > 0:
            # Global conditioning
            global_embed_dim = global_cond_dim if not project_global_cond else embed_dim
            self.to_global_embed = nn.Sequential(
                operations.Linear(global_cond_dim, global_embed_dim, bias=False, dtype=dtype, device=device),
                nn.SiLU(),
                operations.Linear(global_embed_dim, global_embed_dim, bias=False, dtype=dtype, device=device)
            )

        if prepend_cond_dim > 0:
            # Prepend conditioning
            self.to_prepend_embed = nn.Sequential(
                operations.Linear(prepend_cond_dim, embed_dim, bias=False, dtype=dtype, device=device),
                nn.SiLU(),
                operations.Linear(embed_dim, embed_dim, bias=False, dtype=dtype, device=device)
            )

        self.input_concat_dim = input_concat_dim

        dim_in = io_channels + self.input_concat_dim

        self.patch_size = patch_size

        # Transformer

        self.transformer_type = transformer_type

        self.global_cond_type = global_cond_type

        if self.transformer_type == "continuous_transformer":

            global_dim = None

            if self.global_cond_type == "adaLN":
                # The global conditioning is projected to the embed_dim already at this point
                global_dim = embed_dim

            self.transformer = ContinuousTransformer(
                dim=embed_dim,
                depth=depth,
                dim_heads=embed_dim // num_heads,
                dim_in=dim_in * patch_size,
                dim_out=io_channels * patch_size,
                cross_attend = cond_token_dim > 0,
                cond_token_dim = cond_embed_dim,
                global_cond_dim=global_dim,
                dtype=dtype,
                device=device,
                operations=operations,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown transformer type: {self.transformer_type}")

        self.preprocess_conv = operations.Conv1d(dim_in, dim_in, 1, bias=False, dtype=dtype, device=device)
        self.postprocess_conv = operations.Conv1d(io_channels, io_channels, 1, bias=False, dtype=dtype, device=device)