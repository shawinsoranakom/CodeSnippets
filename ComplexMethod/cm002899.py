def __init__(self, config):
        super().__init__()
        if config.hidden_size % config.num_attention_heads != 0 and not hasattr(config, "embedding_size"):
            raise ValueError(
                f"The hidden size ({config.hidden_size}) is not a multiple of the number of attention "
                f"heads ({config.num_attention_heads})"
            )
        kernel_loaded = lsh_cumulation is not None
        if is_torch_cuda_available() and is_ninja_available() and not kernel_loaded:
            try:
                load_cuda_kernels()
            except Exception as e:
                logger.warning(f"Could not load the custom kernel for multi-scale deformable attention: {e}")

        self.num_attention_heads = config.num_attention_heads
        self.attention_head_size = int(config.hidden_size / config.num_attention_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        self.query = nn.Linear(config.hidden_size, self.all_head_size)
        self.key = nn.Linear(config.hidden_size, self.all_head_size)
        self.value = nn.Linear(config.hidden_size, self.all_head_size)

        self.dropout = nn.Dropout(config.attention_probs_dropout_prob)

        self.use_expectation = config.use_expectation
        self.hash_code_len = config.hash_code_len
        self.use_conv = config.conv_window is not None
        self.use_fast_hash = config.use_fast_hash
        self.num_hash = config.num_hash
        self.lsh_backward = config.lsh_backward

        self.lsh_config = {
            "hash_code_len": self.hash_code_len,
            "use_fast_hash": self.use_fast_hash,
            "num_hash": self.num_hash,
            "lsh_backward": self.lsh_backward,
        }

        if config.conv_window is not None:
            self.conv = nn.Conv2d(
                in_channels=config.num_attention_heads,
                out_channels=config.num_attention_heads,
                kernel_size=(config.conv_window, 1),
                padding=(config.conv_window // 2, 0),
                bias=False,
                groups=config.num_attention_heads,
            )