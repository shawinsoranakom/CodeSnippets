def __init__(
        self,
        dim = None,
        max_position_embeddings = 2048,
        base = 10000,
        device = None,
        config = None,  # [TODO] Hack to pass in config - need to remove later
    ):
        super().__init__()
        # In transformers 5.0+, RotaryEmbedding(config) passes config as first positional arg (dim)
        if (
            config is None
            and dim is not None
            and hasattr(dim, "max_position_embeddings")
        ):
            config = dim
            dim = None
        if config is not None:
            # [TODO] Hack to pass in config - need to remove later
            base = _get_rope_theta(config, default = base)
            partial_rotary_factor = (
                config.partial_rotary_factor
                if hasattr(config, "partial_rotary_factor")
                else 1.0
            )
            dim = getattr(config, "head_dim", None)
            if dim is None:
                dim = int((config.hidden_size // config.num_attention_heads))
            device = "cuda"
            max_position_embeddings = config.max_position_embeddings
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        # Dynamic RoPE we first set it to a max of 4 * 8192 tokens then we iteratively grow this
        self.current_rope_size = min(4 * 8192, self.max_position_embeddings)
        self.multi_gpu_cos_cached = [None] * DEVICE_COUNT
        self.multi_gpu_sin_cached = [None] * DEVICE_COUNT

        # Build here to make `torch.jit.trace` work.
        for device in range(DEVICE_COUNT):
            self._set_cos_sin_cache(
                seq_len = self.current_rope_size,
                device = torch.device(device),
                dtype = torch.get_default_dtype(),
            )

        # dummy so that patch_utils doesn't fail for now
        self.cos_cached = torch.empty(
            1, device = torch.cuda.current_device(), dtype = torch.get_default_dtype()
        )
        self.sin_cached = torch.empty(
            1, device = torch.cuda.current_device(), dtype = torch.get_default_dtype()
        )