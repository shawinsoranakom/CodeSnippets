def __init__(
        self,
        channels,
        emb_channels,
        dropout,
        out_channels=None,
        use_conv=False,
        use_scale_shift_norm=False,
        dims=2,
        use_checkpoint=False,
        up=False,
        down=False,
        kernel_size=3,
        exchange_temb_dims=False,
        skip_t_emb=False,
        dtype=None,
        device=None,
        operations=ops
    ):
        super().__init__()
        self.channels = channels
        self.emb_channels = emb_channels
        self.dropout = dropout
        self.out_channels = out_channels or channels
        self.use_conv = use_conv
        self.use_checkpoint = use_checkpoint
        self.use_scale_shift_norm = use_scale_shift_norm
        self.exchange_temb_dims = exchange_temb_dims

        if isinstance(kernel_size, list):
            padding = [k // 2 for k in kernel_size]
        else:
            padding = kernel_size // 2

        self.in_layers = nn.Sequential(
            operations.GroupNorm(32, channels, dtype=dtype, device=device),
            nn.SiLU(),
            operations.conv_nd(dims, channels, self.out_channels, kernel_size, padding=padding, dtype=dtype, device=device),
        )

        self.updown = up or down

        if up:
            self.h_upd = Upsample(channels, False, dims, dtype=dtype, device=device)
            self.x_upd = Upsample(channels, False, dims, dtype=dtype, device=device)
        elif down:
            self.h_upd = Downsample(channels, False, dims, dtype=dtype, device=device)
            self.x_upd = Downsample(channels, False, dims, dtype=dtype, device=device)
        else:
            self.h_upd = self.x_upd = nn.Identity()

        self.skip_t_emb = skip_t_emb
        if self.skip_t_emb:
            self.emb_layers = None
            self.exchange_temb_dims = False
        else:
            self.emb_layers = nn.Sequential(
                nn.SiLU(),
                operations.Linear(
                    emb_channels,
                    2 * self.out_channels if use_scale_shift_norm else self.out_channels, dtype=dtype, device=device
                ),
            )
        self.out_layers = nn.Sequential(
            operations.GroupNorm(32, self.out_channels, dtype=dtype, device=device),
            nn.SiLU(),
            nn.Dropout(p=dropout),
            operations.conv_nd(dims, self.out_channels, self.out_channels, kernel_size, padding=padding, dtype=dtype, device=device)
            ,
        )

        if self.out_channels == channels:
            self.skip_connection = nn.Identity()
        elif use_conv:
            self.skip_connection = operations.conv_nd(
                dims, channels, self.out_channels, kernel_size, padding=padding, dtype=dtype, device=device
            )
        else:
            self.skip_connection = operations.conv_nd(dims, channels, self.out_channels, 1, dtype=dtype, device=device)