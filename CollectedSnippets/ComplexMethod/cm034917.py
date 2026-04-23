def __init__(
        self,
        k_at_hops,
        num_adjacent_linkages,
        node_geo_feat_len,
        pooling_scale,
        pooling_output_size,
        nms_thr,
        min_width,
        max_width,
        comp_shrink_ratio,
        comp_w_h_ratio,
        comp_score_thr,
        text_region_thr,
        center_region_thr,
        center_region_area_thr,
    ):
        assert len(k_at_hops) == 2
        assert isinstance(k_at_hops, tuple)
        assert isinstance(num_adjacent_linkages, int)
        assert isinstance(node_geo_feat_len, int)
        assert isinstance(pooling_scale, float)
        assert isinstance(pooling_output_size, tuple)
        assert isinstance(nms_thr, float)
        assert isinstance(min_width, float)
        assert isinstance(max_width, float)
        assert isinstance(comp_shrink_ratio, float)
        assert isinstance(comp_w_h_ratio, float)
        assert isinstance(comp_score_thr, float)
        assert isinstance(text_region_thr, float)
        assert isinstance(center_region_thr, float)
        assert isinstance(center_region_area_thr, int)

        self.k_at_hops = k_at_hops
        self.active_connection = num_adjacent_linkages
        self.local_graph_depth = len(self.k_at_hops)
        self.node_geo_feat_dim = node_geo_feat_len
        self.pooling = RoIAlignRotated(pooling_output_size, pooling_scale)
        self.nms_thr = nms_thr
        self.min_width = min_width
        self.max_width = max_width
        self.comp_shrink_ratio = comp_shrink_ratio
        self.comp_w_h_ratio = comp_w_h_ratio
        self.comp_score_thr = comp_score_thr
        self.text_region_thr = text_region_thr
        self.center_region_thr = center_region_thr
        self.center_region_area_thr = center_region_area_thr