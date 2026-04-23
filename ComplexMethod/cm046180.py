def __init__(
        self,
        d_model: int,
        frozen: bool,
        interaction_layer,
        layer,
        num_layers: int,
        num_queries: int,
        return_intermediate: bool,
        box_refine: bool = False,
        num_o2m_queries: int = 0,
        dac: bool = False,
        boxRPB: str = "none",
        # Experimental: An object query for SAM 2 tasks
        instance_query: bool = False,
        # Defines the number of additional instance queries,
        # 1 or 4 are the most likely for single vs multi mask support
        num_instances: int = 1,  # Irrelevant if instance_query is False
        dac_use_selfatt_ln: bool = True,
        use_act_checkpoint: bool = False,
        compile_mode=None,
        presence_token: bool = False,
        clamp_presence_logits: bool = True,
        clamp_presence_logit_max_val: float = 10.0,
        use_normed_output_consistently: bool = True,
        separate_box_head_instance: bool = False,
        separate_norm_instance: bool = False,
    ):
        """Initialize the TransformerDecoder."""
        super().__init__()
        self.d_model = d_model
        self.layers = _get_clones(layer, num_layers)
        self.fine_layers = (
            _get_clones(interaction_layer, num_layers) if interaction_layer is not None else [None] * num_layers
        )
        self.num_layers = num_layers
        self.num_queries = num_queries
        self.dac = dac
        if dac:
            self.num_o2m_queries = num_queries
            tot_num_queries = num_queries
        else:
            self.num_o2m_queries = num_o2m_queries
            tot_num_queries = num_queries + num_o2m_queries
        self.norm = nn.LayerNorm(d_model)
        self.return_intermediate = return_intermediate
        self.bbox_embed = MLP(d_model, d_model, 4, 3)
        self.query_embed = nn.Embedding(tot_num_queries, d_model)
        self.instance_query_embed = None
        self.instance_query_reference_points = None
        self.use_instance_query = instance_query
        self.num_instances = num_instances
        self.use_normed_output_consistently = use_normed_output_consistently

        self.instance_norm = nn.LayerNorm(d_model) if separate_norm_instance else None
        self.instance_bbox_embed = None
        if separate_box_head_instance:
            self.instance_bbox_embed = MLP(d_model, d_model, 4, 3)
        if instance_query:
            self.instance_query_embed = nn.Embedding(num_instances, d_model)
        self.box_refine = box_refine
        if box_refine:
            nn.init.constant_(self.bbox_embed.layers[-1].weight.data, 0)
            nn.init.constant_(self.bbox_embed.layers[-1].bias.data, 0)

            self.reference_points = nn.Embedding(num_queries, 4)
            if instance_query:
                self.instance_reference_points = nn.Embedding(num_instances, 4)

        assert boxRPB in ["none", "log", "linear", "both"]
        self.boxRPB = boxRPB
        if boxRPB != "none":
            try:
                nheads = self.layers[0].cross_attn_image.num_heads
            except AttributeError:
                nheads = self.layers[0].cross_attn.num_heads

            n_input = 4 if boxRPB == "both" else 2
            self.boxRPB_embed_x = MLP(n_input, d_model, nheads, 2)
            self.boxRPB_embed_y = MLP(n_input, d_model, nheads, 2)
            self.compilable_cord_cache = None
            self.compilable_stored_size = None
            self.coord_cache = {}

        self.roi_pooler = (
            RoIAlign(output_size=7, spatial_scale=1, sampling_ratio=-1, aligned=True)
            if interaction_layer is not None
            else None
        )
        if frozen:
            for p in self.parameters():
                p.requires_grad_(False)

        self.presence_token = None
        self.clamp_presence_logits = clamp_presence_logits
        self.clamp_presence_logit_max_val = clamp_presence_logit_max_val
        if presence_token:
            self.presence_token = nn.Embedding(1, d_model)
            self.presence_token_head = MLP(d_model, d_model, 1, 3)
            self.presence_token_out_norm = nn.LayerNorm(d_model)

        self.ref_point_head = MLP(2 * self.d_model, self.d_model, self.d_model, 2)
        self.dac_use_selfatt_ln = dac_use_selfatt_ln
        self.use_act_checkpoint = use_act_checkpoint

        nn.init.normal_(self.query_embed.weight.data)
        if self.instance_query_embed is not None:
            nn.init.normal_(self.instance_query_embed.weight.data)

        assert self.roi_pooler is None
        assert self.return_intermediate, "support return_intermediate only"
        assert self.box_refine, "support box refine only"

        self.compile_mode = compile_mode
        self.compiled = False
        # We defer compilation till after the first forward, to first warm-up the boxRPB cache

        # assign layer index to each layer so that some layers can decide what to do
        # based on which layer index they are (e.g. cross attention to memory bank only
        # in selected layers)
        for layer_idx, layer in enumerate(self.layers):
            layer.layer_idx = layer_idx