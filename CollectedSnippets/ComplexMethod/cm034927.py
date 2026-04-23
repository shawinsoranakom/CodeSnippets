def __init__(
        self,
        in_channels,
        k_at_hops=(8, 4),
        num_adjacent_linkages=3,
        node_geo_feat_len=120,
        pooling_scale=1.0,
        pooling_output_size=(4, 3),
        nms_thr=0.3,
        min_width=8.0,
        max_width=24.0,
        comp_shrink_ratio=1.03,
        comp_ratio=0.4,
        comp_score_thr=0.3,
        text_region_thr=0.2,
        center_region_thr=0.2,
        center_region_area_thr=50,
        local_graph_thr=0.7,
        **kwargs,
    ):
        super().__init__()

        assert isinstance(in_channels, int)
        assert isinstance(k_at_hops, tuple)
        assert isinstance(num_adjacent_linkages, int)
        assert isinstance(node_geo_feat_len, int)
        assert isinstance(pooling_scale, float)
        assert isinstance(pooling_output_size, tuple)
        assert isinstance(comp_shrink_ratio, float)
        assert isinstance(nms_thr, float)
        assert isinstance(min_width, float)
        assert isinstance(max_width, float)
        assert isinstance(comp_ratio, float)
        assert isinstance(comp_score_thr, float)
        assert isinstance(text_region_thr, float)
        assert isinstance(center_region_thr, float)
        assert isinstance(center_region_area_thr, int)
        assert isinstance(local_graph_thr, float)

        self.in_channels = in_channels
        self.out_channels = 6
        self.downsample_ratio = 1.0
        self.k_at_hops = k_at_hops
        self.num_adjacent_linkages = num_adjacent_linkages
        self.node_geo_feat_len = node_geo_feat_len
        self.pooling_scale = pooling_scale
        self.pooling_output_size = pooling_output_size
        self.comp_shrink_ratio = comp_shrink_ratio
        self.nms_thr = nms_thr
        self.min_width = min_width
        self.max_width = max_width
        self.comp_ratio = comp_ratio
        self.comp_score_thr = comp_score_thr
        self.text_region_thr = text_region_thr
        self.center_region_thr = center_region_thr
        self.center_region_area_thr = center_region_area_thr
        self.local_graph_thr = local_graph_thr

        self.out_conv = nn.Conv2D(
            in_channels=self.in_channels,
            out_channels=self.out_channels,
            kernel_size=1,
            stride=1,
            padding=0,
        )

        self.graph_train = LocalGraphs(
            self.k_at_hops,
            self.num_adjacent_linkages,
            self.node_geo_feat_len,
            self.pooling_scale,
            self.pooling_output_size,
            self.local_graph_thr,
        )

        self.graph_test = ProposalLocalGraphs(
            self.k_at_hops,
            self.num_adjacent_linkages,
            self.node_geo_feat_len,
            self.pooling_scale,
            self.pooling_output_size,
            self.nms_thr,
            self.min_width,
            self.max_width,
            self.comp_shrink_ratio,
            self.comp_ratio,
            self.comp_score_thr,
            self.text_region_thr,
            self.center_region_thr,
            self.center_region_area_thr,
        )

        pool_w, pool_h = self.pooling_output_size
        node_feat_len = (pool_w * pool_h) * (
            self.in_channels + self.out_channels
        ) + self.node_geo_feat_len
        self.gcn = GCN(node_feat_len)