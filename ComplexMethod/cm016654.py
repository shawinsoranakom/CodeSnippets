def __init__(self, in_channels=(512, 1024, 2048), feat_strides=(8, 16, 32), hidden_dim=256, nhead=8, dim_feedforward=2048, use_encoder_idx=(2,), num_encoder_layers=1,
                 pe_temperature=10000, expansion=1.0, depth_mult=1.0, act='silu', eval_spatial_size=(640, 640), device=None, dtype=None, operations=None):
        super().__init__()
        self.in_channels       = list(in_channels)
        self.feat_strides      = list(feat_strides)
        self.hidden_dim        = hidden_dim
        self.use_encoder_idx   = list(use_encoder_idx)
        self.pe_temperature    = pe_temperature
        self.eval_spatial_size = eval_spatial_size
        self.out_channels      = [hidden_dim] * len(in_channels)
        self.out_strides       = list(feat_strides)

        # channel projection (expects pre-fused weights)
        self.input_proj = nn.ModuleList([
            nn.Sequential(OrderedDict([('conv', operations.Conv2d(ch, hidden_dim, 1, bias=True, device=device, dtype=dtype))]))
            for ch in in_channels
        ])

        # AIFI transformer — use _TransformerEncoder so keys are  encoder.0.layers.N.*
        self.encoder = nn.ModuleList([
            _TransformerEncoder(num_encoder_layers, hidden_dim, nhead, dim_feedforward, device=device, dtype=dtype, operations=operations)
            for _ in range(len(use_encoder_idx))
        ])

        nb  = round(3 * depth_mult)
        exp = expansion

        # top-down FPN  (dfine: lateral conv has no act)
        self.lateral_convs = nn.ModuleList(
            [ConvNormLayer(hidden_dim, hidden_dim, 1, 1, device=device, dtype=dtype, operations=operations)
             for _ in range(len(in_channels) - 1)])
        self.fpn_blocks = nn.ModuleList(
            [RepNCSPELAN4(hidden_dim * 2, hidden_dim, hidden_dim * 2, round(exp * hidden_dim // 2), nb, act=act, device=device, dtype=dtype, operations=operations)
             for _ in range(len(in_channels) - 1)])

        # bottom-up PAN  (dfine: nn.Sequential(SCDown) — keeps checkpoint key  .0.cv1/.0.cv2)
        self.downsample_convs = nn.ModuleList(
            [nn.Sequential(SCDown(hidden_dim, hidden_dim, 3, 2, device=device, dtype=dtype, operations=operations))
             for _ in range(len(in_channels) - 1)])
        self.pan_blocks = nn.ModuleList(
            [RepNCSPELAN4(hidden_dim * 2, hidden_dim, hidden_dim * 2, round(exp * hidden_dim // 2), nb, act=act, device=device, dtype=dtype, operations=operations)
             for _ in range(len(in_channels) - 1)])

        # cache positional embeddings for fixed spatial size
        if eval_spatial_size:
            for idx in self.use_encoder_idx:
                stride = self.feat_strides[idx]
                pe = self._build_pe(eval_spatial_size[1] // stride,
                                    eval_spatial_size[0] // stride,
                                    hidden_dim, pe_temperature)
                setattr(self, f'pos_embed{idx}', pe)