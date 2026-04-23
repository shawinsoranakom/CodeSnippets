def __init__(self,
                 dim=2048,
                 num_heads=32,
                 inject_layer=[0, 27],
                 root_net=None,
                 enable_adain=False,
                 adain_dim=2048,
                 adain_mode=None,
                 dtype=None,
                 device=None,
                 operations=None):
        super().__init__()
        self.enable_adain = enable_adain
        self.adain_mode = adain_mode
        self.injected_block_id = {}
        audio_injector_id = 0
        for inject_id in inject_layer:
            self.injected_block_id[inject_id] = audio_injector_id
            audio_injector_id += 1

        self.injector = nn.ModuleList([
            WanT2VCrossAttention(
                dim=dim,
                num_heads=num_heads,
                qk_norm=True, operation_settings={"operations": operations, "device": device, "dtype": dtype}
            ) for _ in range(audio_injector_id)
        ])
        self.injector_pre_norm_feat = nn.ModuleList([
            operations.LayerNorm(
                dim,
                elementwise_affine=False,
                eps=1e-6, dtype=dtype, device=device
            ) for _ in range(audio_injector_id)
        ])
        self.injector_pre_norm_vec = nn.ModuleList([
            operations.LayerNorm(
                dim,
                elementwise_affine=False,
                eps=1e-6, dtype=dtype, device=device
            ) for _ in range(audio_injector_id)
        ])
        if enable_adain:
            self.injector_adain_layers = nn.ModuleList([
                AdaLayerNorm(
                    output_dim=dim * 2, embedding_dim=adain_dim, dtype=dtype, device=device, operations=operations)
                for _ in range(audio_injector_id)
            ])
            if adain_mode != "attn_norm":
                self.injector_adain_output_layers = nn.ModuleList(
                    [operations.Linear(dim, dim, dtype=dtype, device=device) for _ in range(audio_injector_id)])