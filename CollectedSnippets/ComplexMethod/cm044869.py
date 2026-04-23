def __init__(
        self,
        dim,
        *,
        depth,
        stereo=False,
        num_stems=1,
        time_transformer_depth=2,
        freq_transformer_depth=2,
        linear_transformer_depth=0,
        freqs_per_bands: Tuple[int, ...] = DEFAULT_FREQS_PER_BANDS,
        # in the paper, they divide into ~60 bands, test with 1 for starters
        dim_head=64,
        heads=8,
        attn_dropout=0.0,
        ff_dropout=0.0,
        flash_attn=True,
        dim_freqs_in=1025,
        stft_n_fft=2048,
        stft_hop_length=512,
        # 10ms at 44100Hz, from sections 4.1, 4.4 in the paper - @faroit recommends // 2 or // 4 for better reconstruction
        stft_win_length=2048,
        stft_normalized=False,
        stft_window_fn: Optional[Callable] = None,
        mask_estimator_depth=2,
        multi_stft_resolution_loss_weight=1.0,
        multi_stft_resolutions_window_sizes: Tuple[int, ...] = (4096, 2048, 1024, 512, 256),
        multi_stft_hop_size=147,
        multi_stft_normalized=False,
        multi_stft_window_fn: Callable = torch.hann_window,
        mlp_expansion_factor=4,
        use_torch_checkpoint=False,
        skip_connection=False,
    ):
        super().__init__()

        self.stereo = stereo
        self.audio_channels = 2 if stereo else 1
        self.num_stems = num_stems
        self.use_torch_checkpoint = use_torch_checkpoint
        self.skip_connection = skip_connection

        self.layers = ModuleList([])

        transformer_kwargs = dict(
            dim=dim,
            heads=heads,
            dim_head=dim_head,
            attn_dropout=attn_dropout,
            ff_dropout=ff_dropout,
            flash_attn=flash_attn,
            norm_output=False,
        )

        time_rotary_embed = RotaryEmbedding(dim=dim_head)
        freq_rotary_embed = RotaryEmbedding(dim=dim_head)

        for _ in range(depth):
            tran_modules = []
            if linear_transformer_depth > 0:
                tran_modules.append(Transformer(depth=linear_transformer_depth, linear_attn=True, **transformer_kwargs))
            tran_modules.append(
                Transformer(depth=time_transformer_depth, rotary_embed=time_rotary_embed, **transformer_kwargs)
            )
            tran_modules.append(
                Transformer(depth=freq_transformer_depth, rotary_embed=freq_rotary_embed, **transformer_kwargs)
            )
            self.layers.append(nn.ModuleList(tran_modules))

        self.final_norm = RMSNorm(dim)

        self.stft_kwargs = dict(
            n_fft=stft_n_fft, hop_length=stft_hop_length, win_length=stft_win_length, normalized=stft_normalized
        )

        self.stft_window_fn = partial(default(stft_window_fn, torch.hann_window), stft_win_length)

        freqs = torch.stft(
            torch.randn(1, 4096), **self.stft_kwargs, window=torch.ones(stft_win_length), return_complex=True
        ).shape[1]

        assert len(freqs_per_bands) > 1
        assert sum(freqs_per_bands) == freqs, (
            f"the number of freqs in the bands must equal {freqs} based on the STFT settings, but got {sum(freqs_per_bands)}"
        )

        freqs_per_bands_with_complex = tuple(2 * f * self.audio_channels for f in freqs_per_bands)

        self.band_split = BandSplit(dim=dim, dim_inputs=freqs_per_bands_with_complex)

        self.mask_estimators = nn.ModuleList([])

        for _ in range(num_stems):
            mask_estimator = MaskEstimator(
                dim=dim,
                dim_inputs=freqs_per_bands_with_complex,
                depth=mask_estimator_depth,
                mlp_expansion_factor=mlp_expansion_factor,
            )

            self.mask_estimators.append(mask_estimator)

        # for the multi-resolution stft loss

        self.multi_stft_resolution_loss_weight = multi_stft_resolution_loss_weight
        self.multi_stft_resolutions_window_sizes = multi_stft_resolutions_window_sizes
        self.multi_stft_n_fft = stft_n_fft
        self.multi_stft_window_fn = multi_stft_window_fn

        self.multi_stft_kwargs = dict(hop_length=multi_stft_hop_size, normalized=multi_stft_normalized)