def __init__(self, *, vllm_config: VllmConfig):
        super().__init__()

        self.hf_config = vllm_config.model_config.hf_config

        feat_in = self.hf_config.encoder["feat_in"]
        n_layers = self.hf_config.encoder["n_layers"]
        d_model = self.hf_config.encoder["d_model"]
        feat_out = self.hf_config.encoder["feat_out"]
        causal_downsampling = self.hf_config.encoder["causal_downsampling"]
        subsampling = self.hf_config.encoder["subsampling"]
        subsampling_factor = self.hf_config.encoder["subsampling_factor"]
        subsampling_conv_chunking_factor = self.hf_config.encoder.get(
            "subsampling_conv_chunking_factor", 1
        )
        subsampling_conv_channels = self.hf_config.encoder["subsampling_conv_channels"]
        ff_expansion_factor = self.hf_config.encoder["ff_expansion_factor"]
        self_attention_model = self.hf_config.encoder["self_attention_model"]
        n_heads = self.hf_config.encoder["n_heads"]
        att_context_size = self.hf_config.encoder["att_context_size"]
        att_context_probs = self.hf_config.encoder.get("att_context_probs", None)
        att_context_style = self.hf_config.encoder.get("att_context_style", "regular")
        xscaling = self.hf_config.encoder["xscaling"]
        untie_biases = self.hf_config.encoder["untie_biases"]
        pos_emb_max_len = self.hf_config.encoder["pos_emb_max_len"]
        conv_kernel_size = self.hf_config.encoder["conv_kernel_size"]
        conv_norm_type = self.hf_config.encoder["conv_norm_type"]
        conv_context_size = self.hf_config.encoder["conv_context_size"]
        use_bias = self.hf_config.encoder.get("use_bias", True)

        d_ff = d_model * ff_expansion_factor
        self.d_model = d_model
        self._feat_in = feat_in
        self.att_context_style = att_context_style
        self.subsampling_factor = subsampling_factor

        self.self_attention_model = self_attention_model

        # Setting up the att_context_size
        (
            _,
            self.att_context_size,
            _,
            self.conv_context_size,
        ) = self._calc_context_sizes(
            att_context_style=att_context_style,
            att_context_size=att_context_size,
            att_context_probs=att_context_probs,
            conv_context_size=conv_context_size,
            conv_kernel_size=conv_kernel_size,
        )

        if xscaling:
            self.xscale = math.sqrt(d_model)
        else:
            self.xscale = None

        # Subsampling
        if subsampling_conv_channels == -1:
            subsampling_conv_channels = d_model
        assert subsampling and subsampling_factor > 1 and subsampling == "dw_striding"

        self.pre_encode = ConvSubsampling(
            subsampling=subsampling,
            subsampling_factor=subsampling_factor,
            feat_in=feat_in,
            feat_out=d_model,
            conv_channels=subsampling_conv_channels,
            subsampling_conv_chunking_factor=subsampling_conv_chunking_factor,
            activation=nn.ReLU(True),
            is_causal=causal_downsampling,
        )

        self._feat_out = d_model

        # Biases for relative positional encoding
        if not untie_biases and self_attention_model == "rel_pos":
            d_head = d_model // n_heads
            # Register as buffers instead of parameters since they're not trainable
            # and need to respect dtype during weight loading
            self.register_buffer(
                "pos_bias_u", torch.zeros(n_heads, d_head), persistent=True
            )
            self.register_buffer(
                "pos_bias_v", torch.zeros(n_heads, d_head), persistent=True
            )
            pos_bias_u = self.pos_bias_u
            pos_bias_v = self.pos_bias_v
        else:
            pos_bias_u = None
            pos_bias_v = None

        # Positional encodings
        self.pos_emb_max_len = pos_emb_max_len
        assert self_attention_model == "rel_pos"
        self.pos_enc = RelPositionalEncoding(
            d_model=d_model,
            max_len=pos_emb_max_len,
            xscale=self.xscale,
        )

        self.layers = nn.ModuleList()
        for i in range(n_layers):
            layer = ConformerLayer(
                d_model=d_model,
                d_ff=d_ff,
                self_attention_model=self_attention_model,
                n_heads=n_heads,
                conv_kernel_size=conv_kernel_size,
                conv_norm_type=conv_norm_type,
                conv_context_size=self.conv_context_size,
                pos_bias_u=pos_bias_u,
                pos_bias_v=pos_bias_v,
                att_context_size=self.att_context_size,
                use_bias=use_bias,
            )
            self.layers.append(layer)

        if feat_out > 0 and feat_out != self._feat_out:
            self.out_proj = nn.Linear(self._feat_out, feat_out)
            self._feat_out = feat_out
        else:
            self.out_proj = None
            self._feat_out = d_model
        self.set_max_audio_length(self.pos_emb_max_len)