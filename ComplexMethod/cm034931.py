def __init__(
        self,
        k_at_hops,
        num_adjacent_linkages,
        node_geo_feat_len,
        pooling_scale,
        pooling_output_size,
        local_graph_thr,
    ):
        assert len(k_at_hops) == 2
        assert all(isinstance(n, int) for n in k_at_hops)
        assert isinstance(num_adjacent_linkages, int)
        assert isinstance(node_geo_feat_len, int)
        assert isinstance(pooling_scale, float)
        assert all(isinstance(n, int) for n in pooling_output_size)
        assert isinstance(local_graph_thr, float)

        self.k_at_hops = k_at_hops
        self.num_adjacent_linkages = num_adjacent_linkages
        self.node_geo_feat_dim = node_geo_feat_len
        self.pooling = RoIAlignRotated(pooling_output_size, pooling_scale)
        self.local_graph_thr = local_graph_thr