def __post_init__(self, **kwargs):
        self.image_size = self.image_size if self.image_size is not None else [1024, 1024]
        self.patch_kernel_size = self.patch_kernel_size if self.patch_kernel_size is not None else [7, 7]
        self.patch_stride = self.patch_stride if self.patch_stride is not None else [4, 4]
        self.patch_padding = self.patch_padding if self.patch_padding is not None else [3, 3]
        self.query_stride = self.query_stride if self.query_stride is not None else [2, 2]
        self.window_positional_embedding_background_size = (
            self.window_positional_embedding_background_size
            if self.window_positional_embedding_background_size is not None
            else [7, 7]
        )
        self.blocks_per_stage = self.blocks_per_stage if self.blocks_per_stage is not None else [1, 2, 7, 2]
        self.embed_dim_per_stage = (
            self.embed_dim_per_stage if self.embed_dim_per_stage is not None else [96, 192, 384, 768]
        )
        self.num_attention_heads_per_stage = (
            self.num_attention_heads_per_stage if self.num_attention_heads_per_stage is not None else [1, 2, 4, 8]
        )
        self.window_size_per_stage = (
            self.window_size_per_stage if self.window_size_per_stage is not None else [8, 4, 14, 7]
        )
        self.global_attention_blocks = (
            self.global_attention_blocks if self.global_attention_blocks is not None else [5, 7, 9]
        )
        super().__post_init__(**kwargs)