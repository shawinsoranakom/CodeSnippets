def __init__(
        self,
        dim = None,
        max_position_embeddings = 131072,
        original_max_position_embeddings = 4096,
        base = 10000,
        short_factor = None,
        long_factor = None,
        device = None,
        config = None,  # [TODO] Hack to pass in config - need to remove later
    ):
        super().__init__()
        assert short_factor is not None
        assert long_factor is not None
        assert type(original_max_position_embeddings) is int

        if config is not None:
            # [TODO] Hack to pass in config - need to remove later
            base = _get_rope_theta(config, default = base)
            partial_rotary_factor = (
                config.partial_rotary_factor
                if hasattr(config, "partial_rotary_factor")
                else 1.0
            )
            dim = int((config.hidden_size // config.num_attention_heads))
            device = DEVICE_TYPE_TORCH
            max_position_embeddings = config.max_position_embeddings

        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.original_max_position_embeddings = original_max_position_embeddings
        self.base = base
        # Dynamic RoPE we first set it to a max of 4 * 8192 tokens then we iteratively grow this
        self.current_rope_size = min(
            original_max_position_embeddings, self.max_position_embeddings
        )
        self.multi_gpu_short_cos_cached = [None] * DEVICE_COUNT
        self.multi_gpu_short_sin_cached = [None] * DEVICE_COUNT
        self.multi_gpu_long_cos_cached = [None] * DEVICE_COUNT
        self.multi_gpu_long_sin_cached = [None] * DEVICE_COUNT

        # Long RoPE similar to RoPE except short sequences have 1 cos / sin
        # and long sequences have another cos / sin
        inv_freq_shape = (
            torch.arange(0, self.dim, 2, dtype = torch.int64, device = "cpu").float()
            / self.dim
        )
        short_factor = torch.tensor(short_factor, device = "cpu", dtype = torch.float32)
        long_factor = torch.tensor(long_factor, device = "cpu", dtype = torch.float32)
        short_inv_freq = 1.0 / (short_factor * self.base**inv_freq_shape)
        long_inv_freq = 1.0 / (long_factor * self.base**inv_freq_shape)

        # Phi-3 Scale factor
        scale = self.max_position_embeddings / self.original_max_position_embeddings
        if scale <= 1.0:
            scaling_factor = 1.0
        else:
            scaling_factor = math.sqrt(
                1 + math.log(scale) / math.log(self.original_max_position_embeddings)
            )
        self.scaling_factor = scaling_factor

        # Short and long inv_freq
        self.register_buffer("short_inv_freq", short_inv_freq, persistent = False)
        self.register_buffer("long_inv_freq", long_inv_freq, persistent = False)

        # Build here to make `torch.jit.trace` work.
        # Initialize short sequences cache for all devices
        dtype = torch.bfloat16 if is_bfloat16_supported() else torch.float16
        t = torch.arange(
            original_max_position_embeddings,
            device = self.short_inv_freq.device,
            dtype = torch.int64,
        ).float()
        freqs = torch.outer(t, self.short_inv_freq)
        emb = torch.cat((freqs, freqs), dim = -1)

        for device_idx in range(DEVICE_COUNT):
            device_obj = torch.device(device_idx)
            cos_cached = (emb.cos() * self.scaling_factor).to(
                dtype = dtype, device = device_obj, non_blocking = True
            )
            sin_cached = (emb.sin() * self.scaling_factor).to(
                dtype = dtype, device = device_obj, non_blocking = True
            )
            self.multi_gpu_short_cos_cached[device_idx] = cos_cached
            self.multi_gpu_short_sin_cached[device_idx] = sin_cached

        # dummy so that patch_utils doesn't fail for now
        self.short_cos_cached = torch.empty(
            1, device = get_current_device(), dtype = torch.get_default_dtype()
        )
        self.short_sin_cached = torch.empty(
            1, device = get_current_device(), dtype = torch.get_default_dtype()
        )
        self.long_cos_cached = torch.empty(
            1, device = get_current_device(), dtype = torch.get_default_dtype()
        )
        self.long_sin_cached = torch.empty(
            1, device = get_current_device(), dtype = torch.get_default_dtype()
        )