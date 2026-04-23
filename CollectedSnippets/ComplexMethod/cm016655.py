def __init__(self, num_classes=80, hidden_dim=256, num_queries=300, feat_channels=[256, 256, 256], feat_strides=[8, 16, 32],
                 num_levels=3, num_points=[3, 6, 3], nhead=8, num_layers=6, dim_feedforward=1024, eval_idx=-1, eps=1e-2, reg_max=32,
                 reg_scale=8.0, eval_spatial_size=(640, 640), device=None, dtype=None, operations=None):
        super().__init__()
        assert len(feat_strides) == len(feat_channels)
        self.hidden_dim  = hidden_dim
        self.num_queries = num_queries
        self.num_levels  = num_levels
        self.eps         = eps
        self.eval_spatial_size = eval_spatial_size

        self.feat_strides = list(feat_strides)
        for i in range(num_levels - len(feat_strides)):
            self.feat_strides.append(feat_strides[-1] * 2 ** (i + 1))

        # input projection (expects pre-fused weights)
        self.input_proj = nn.ModuleList()
        for ch in feat_channels:
            if ch == hidden_dim:
                self.input_proj.append(nn.Identity())
            else:
                self.input_proj.append(nn.Sequential(OrderedDict([
                    ('conv', operations.Conv2d(ch, hidden_dim, 1, bias=True, device=device, dtype=dtype))])))
        in_ch = feat_channels[-1]
        for i in range(num_levels - len(feat_channels)):
            self.input_proj.append(nn.Sequential(OrderedDict([
                ('conv', operations.Conv2d(in_ch if i == 0 else hidden_dim,
                                           hidden_dim, 3, 2, 1, bias=True, device=device, dtype=dtype))])))
            in_ch = hidden_dim

        # FDR parameters (non-trainable placeholders, set from config)
        self.up        = nn.Parameter(torch.tensor([0.5]),      requires_grad=False)
        self.reg_scale = nn.Parameter(torch.tensor([reg_scale]), requires_grad=False)

        pts = num_points if isinstance(num_points, (list, tuple)) else [num_points] * num_levels
        self.decoder = TransformerDecoder(hidden_dim, nhead, dim_feedforward, num_levels, pts,
                                          num_layers, reg_max, self.reg_scale, self.up, eval_idx, device=device, dtype=dtype, operations=operations)

        self.query_pos_head = MLP(4, 2 * hidden_dim, hidden_dim, 2, device=device, dtype=dtype, operations=operations)
        self.enc_output     = nn.Sequential(OrderedDict([
            ('proj', operations.Linear(hidden_dim, hidden_dim, device=device, dtype=dtype)),
            ('norm', operations.LayerNorm(hidden_dim, device=device, dtype=dtype))]))
        self.enc_score_head = operations.Linear(hidden_dim, num_classes, device=device, dtype=dtype)
        self.enc_bbox_head  = MLP(hidden_dim, hidden_dim, 4, 3, device=device, dtype=dtype, operations=operations)

        self.eval_idx_ = eval_idx if eval_idx >= 0 else num_layers + eval_idx
        self.dec_score_head = nn.ModuleList(
            [operations.Linear(hidden_dim, num_classes, device=device, dtype=dtype) for _ in range(self.eval_idx_ + 1)])
        self.pre_bbox_head  = MLP(hidden_dim, hidden_dim, 4, 3, device=device, dtype=dtype, operations=operations)
        self.dec_bbox_head  = nn.ModuleList(
            [MLP(hidden_dim, hidden_dim, 4 * (reg_max + 1), 3, device=device, dtype=dtype, operations=operations)
             for _ in range(self.eval_idx_ + 1)])
        self.integral = Integral(reg_max)

        if eval_spatial_size:
            # Register as buffers so checkpoint values override the freshly-computed defaults
            anchors, valid_mask = self._gen_anchors()
            self.register_buffer('anchors', anchors)
            self.register_buffer('valid_mask', valid_mask)