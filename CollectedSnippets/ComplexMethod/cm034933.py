def generate_gcn_input(
        self,
        node_feat_batch,
        node_label_batch,
        local_graph_batch,
        knn_batch,
        sorted_dist_ind_batch,
    ):
        """Generate graph convolution network input data.

        Args:
            node_feat_batch (List[Tensor]): The batched graph node features.
            node_label_batch (List[ndarray]): The batched text component
                labels.
            local_graph_batch (List[List[list[int]]]): The local graph node
                indices of image batch.
            knn_batch (List[List[list[int]]]): The knn graph node indices of
                image batch.
            sorted_dist_ind_batch (list[ndarray]): The node indices sorted
                according to the Euclidean distance.

        Returns:
            local_graphs_node_feat (Tensor): The node features of graph.
            adjacent_matrices (Tensor): The adjacent matrices of local graphs.
            pivots_knn_inds (Tensor): The k-nearest neighbor indices in
                local graph.
            gt_linkage (Tensor): The surpervision signal of GCN for linkage
                prediction.
        """
        assert isinstance(node_feat_batch, list)
        assert isinstance(node_label_batch, list)
        assert isinstance(local_graph_batch, list)
        assert isinstance(knn_batch, list)
        assert isinstance(sorted_dist_ind_batch, list)

        num_max_nodes = max(
            [
                len(pivot_local_graph)
                for pivot_local_graphs in local_graph_batch
                for pivot_local_graph in pivot_local_graphs
            ]
        )

        local_graphs_node_feat = []
        adjacent_matrices = []
        pivots_knn_inds = []
        pivots_gt_linkage = []

        for batch_ind, sorted_dist_inds in enumerate(sorted_dist_ind_batch):
            node_feats = node_feat_batch[batch_ind]
            pivot_local_graphs = local_graph_batch[batch_ind]
            pivot_knns = knn_batch[batch_ind]
            node_labels = node_label_batch[batch_ind]

            for graph_ind, pivot_knn in enumerate(pivot_knns):
                pivot_local_graph = pivot_local_graphs[graph_ind]
                num_nodes = len(pivot_local_graph)
                pivot_ind = pivot_local_graph[0]
                node2ind_map = {j: i for i, j in enumerate(pivot_local_graph)}

                knn_inds = paddle.to_tensor([node2ind_map[i] for i in pivot_knn[1:]])
                pivot_feats = node_feats[pivot_ind]
                normalized_feats = (
                    node_feats[paddle.to_tensor(pivot_local_graph)] - pivot_feats
                )

                adjacent_matrix = np.zeros((num_nodes, num_nodes), dtype=np.float32)
                for node in pivot_local_graph:
                    neighbors = sorted_dist_inds[
                        node, 1 : self.num_adjacent_linkages + 1
                    ]
                    for neighbor in neighbors:
                        if neighbor in pivot_local_graph:
                            adjacent_matrix[
                                node2ind_map[node], node2ind_map[neighbor]
                            ] = 1
                            adjacent_matrix[
                                node2ind_map[neighbor], node2ind_map[node]
                            ] = 1

                adjacent_matrix = normalize_adjacent_matrix(adjacent_matrix)
                pad_adjacent_matrix = paddle.zeros((num_max_nodes, num_max_nodes))
                pad_adjacent_matrix[:num_nodes, :num_nodes] = paddle.cast(
                    paddle.to_tensor(adjacent_matrix), "float32"
                )

                pad_normalized_feats = paddle.concat(
                    [
                        normalized_feats,
                        paddle.zeros(
                            (num_max_nodes - num_nodes, normalized_feats.shape[1])
                        ),
                    ],
                    axis=0,
                )
                local_graph_labels = node_labels[pivot_local_graph]
                knn_labels = local_graph_labels[knn_inds.numpy()]
                link_labels = (
                    (node_labels[pivot_ind] == knn_labels)
                    & (node_labels[pivot_ind] > 0)
                ).astype(np.int64)
                link_labels = paddle.to_tensor(link_labels)

                local_graphs_node_feat.append(pad_normalized_feats)
                adjacent_matrices.append(pad_adjacent_matrix)
                pivots_knn_inds.append(knn_inds)
                pivots_gt_linkage.append(link_labels)

        local_graphs_node_feat = paddle.stack(local_graphs_node_feat, 0)
        adjacent_matrices = paddle.stack(adjacent_matrices, 0)
        pivots_knn_inds = paddle.stack(pivots_knn_inds, 0)
        pivots_gt_linkage = paddle.stack(pivots_gt_linkage, 0)

        return (
            local_graphs_node_feat,
            adjacent_matrices,
            pivots_knn_inds,
            pivots_gt_linkage,
        )