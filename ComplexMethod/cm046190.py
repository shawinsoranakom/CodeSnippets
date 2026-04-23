def __init__(
        self,
        encode_boxes_as_points: bool,
        boxes_direct_project: bool,
        boxes_pool: bool,
        boxes_pos_enc: bool,
        d_model: int,
        pos_enc,
        num_layers: int,
        layer: nn.Module,
        roi_size: int = 7,
        add_cls: bool = True,
        add_post_encode_proj: bool = True,
        use_act_ckpt: bool = False,
    ):
        """Initialize the SequenceGeometryEncoder."""
        super().__init__()

        self.d_model = d_model
        self.pos_enc = pos_enc
        self.encode_boxes_as_points = encode_boxes_as_points
        self.roi_size = roi_size

        # Label embeddings: 2 labels if encoding as boxes (pos/neg)
        # 6 labels if encoding as points (regular pos/neg, top-left pos/neg, bottom-right pos/neg)
        num_labels = 6 if self.encode_boxes_as_points else 2
        self.label_embed = torch.nn.Embedding(num_labels, self.d_model)

        # CLS token for pooling
        self.cls_embed = None
        if add_cls:
            self.cls_embed = torch.nn.Embedding(1, self.d_model)

        # Point encoding (used when encode_boxes_as_points is True)
        if encode_boxes_as_points:
            self.points_direct_project = nn.Linear(2, self.d_model)
            self.points_pool_project = None
            self.points_pos_enc_project = None
        else:
            # Box encoding modules
            assert boxes_direct_project or boxes_pos_enc or boxes_pool, "Error: need at least one way to encode boxes"
            self.points_direct_project = None
            self.points_pool_project = None
            self.points_pos_enc_project = None

            self.boxes_direct_project = None
            self.boxes_pool_project = None
            self.boxes_pos_enc_project = None

            if boxes_direct_project:
                self.boxes_direct_project = nn.Linear(4, self.d_model)
            if boxes_pool:
                self.boxes_pool_project = nn.Conv2d(self.d_model, self.d_model, self.roi_size)
            if boxes_pos_enc:
                self.boxes_pos_enc_project = nn.Linear(self.d_model + 2, self.d_model)

        self.final_proj = None
        if add_post_encode_proj:
            self.final_proj = nn.Linear(self.d_model, self.d_model)
            self.norm = nn.LayerNorm(self.d_model)

        self.img_pre_norm = nn.Identity()
        if self.points_pool_project is not None or self.boxes_pool_project is not None:
            self.img_pre_norm = nn.LayerNorm(self.d_model)

        self.encode = None
        if num_layers > 0:
            assert add_cls, "It's currently highly recommended to add a CLS when using a transformer"
            self.encode = _get_clones(layer, num_layers)
            self.encode_norm = nn.LayerNorm(self.d_model)

        self.use_act_ckpt = use_act_ckpt