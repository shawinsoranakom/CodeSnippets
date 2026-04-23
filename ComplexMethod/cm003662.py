def __init__(self, config):
        super().__init__()
        if config.hidden_size % config.num_attention_heads != 0 and not hasattr(config, "embedding_size"):
            raise ValueError(
                f"The hidden size ({config.hidden_size}) is not a multiple of the number of attention "
                f"heads ({config.num_attention_heads})"
            )

        kernel_loaded = mra_cuda_kernel is not None
        if is_torch_cuda_available() and is_cuda_platform() and is_ninja_available() and not kernel_loaded:
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

        self.num_block = (config.max_position_embeddings // 32) * config.block_per_row
        self.num_block = min(self.num_block, int((config.max_position_embeddings // 32) ** 2))

        self.approx_mode = config.approx_mode
        self.initial_prior_first_n_blocks = config.initial_prior_first_n_blocks
        self.initial_prior_diagonal_n_blocks = config.initial_prior_diagonal_n_blocks