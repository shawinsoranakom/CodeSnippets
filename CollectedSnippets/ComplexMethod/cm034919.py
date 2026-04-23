def generate_local_graphs(self, sorted_dist_inds, node_feats):
        """Generate local graphs and graph convolution network input data.

        Args:
            sorted_dist_inds (ndarray): The node indices sorted according to
                the Euclidean distance.
            node_feats (tensor): The features of nodes in graph.

        Returns:
            local_graphs_node_feats (tensor): The features of nodes in local
                graphs.
            adjacent_matrices (tensor): The adjacent matrices.
            pivots_knn_inds (tensor): The k-nearest neighbor indices in
                local graphs.
            pivots_local_graphs (tensor): The indices of nodes in local
                graphs.
        """

        assert sorted_dist_inds.ndim == 2
        assert (
            sorted_dist_inds.shape[0]
            == sorted_dist_inds.shape[1]
            == node_feats.shape[0]
        )

        knn_graph = sorted_dist_inds[:, 1 : self.k_at_hops[0] + 1]
        pivot_local_graphs = []
        pivot_knns = []

        for pivot_ind, knn in enumerate(knn_graph):
            local_graph_neighbors = set(knn)

            for neighbor_ind in knn:
                local_graph_neighbors.update(
                    set(sorted_dist_inds[neighbor_ind, 1 : self.k_at_hops[1] + 1])
                )

            local_graph_neighbors.discard(pivot_ind)
            pivot_local_graph = list(local_graph_neighbors)
            pivot_local_graph.insert(0, pivot_ind)
            pivot_knn = [pivot_ind] + list(knn)

            pivot_local_graphs.append(pivot_local_graph)
            pivot_knns.append(pivot_knn)

        num_max_nodes = max(
            [len(pivot_local_graph) for pivot_local_graph in pivot_local_graphs]
        )

        local_graphs_node_feat = []
        adjacent_matrices = []
        pivots_knn_inds = []
        pivots_local_graphs = []

        for graph_ind, pivot_knn in enumerate(pivot_knns):
            pivot_local_graph = pivot_local_graphs[graph_ind]
            num_nodes = len(pivot_local_graph)
            pivot_ind = pivot_local_graph[0]
            node2ind_map = {j: i for i, j in enumerate(pivot_local_graph)}

            knn_inds = paddle.cast(
                paddle.to_tensor([node2ind_map[i] for i in pivot_knn[1:]]), "int64"
            )
            pivot_feats = node_feats[pivot_ind]
            normalized_feats = (
                node_feats[paddle.to_tensor(pivot_local_graph)] - pivot_feats
            )

            adjacent_matrix = np.zeros((num_nodes, num_nodes), dtype=np.float32)
            for node in pivot_local_graph:
                neighbors = sorted_dist_inds[node, 1 : self.active_connection + 1]
                for neighbor in neighbors:
                    if neighbor in pivot_local_graph:
                        adjacent_matrix[node2ind_map[node], node2ind_map[neighbor]] = 1
                        adjacent_matrix[node2ind_map[neighbor], node2ind_map[node]] = 1

            adjacent_matrix = normalize_adjacent_matrix(adjacent_matrix)
            pad_adjacent_matrix = paddle.zeros(
                (num_max_nodes, num_max_nodes),
            )
            pad_adjacent_matrix[:num_nodes, :num_nodes] = paddle.cast(
                paddle.to_tensor(adjacent_matrix), "float32"
            )

            pad_normalized_feats = paddle.concat(
                [
                    normalized_feats,
                    paddle.zeros(
                        (num_max_nodes - num_nodes, normalized_feats.shape[1]),
                    ),
                ],
                axis=0,
            )

            local_graph_nodes = paddle.to_tensor(pivot_local_graph)
            local_graph_nodes = paddle.concat(
                [
                    local_graph_nodes,
                    paddle.zeros([num_max_nodes - num_nodes], dtype="int64"),
                ],
                axis=-1,
            )

            local_graphs_node_feat.append(pad_normalized_feats)
            adjacent_matrices.append(pad_adjacent_matrix)
            pivots_knn_inds.append(knn_inds)
            pivots_local_graphs.append(local_graph_nodes)

        local_graphs_node_feat = paddle.stack(local_graphs_node_feat, 0)
        adjacent_matrices = paddle.stack(adjacent_matrices, 0)
        pivots_knn_inds = paddle.stack(pivots_knn_inds, 0)
        pivots_local_graphs = paddle.stack(pivots_local_graphs, 0)

        return (
            local_graphs_node_feat,
            adjacent_matrices,
            pivots_knn_inds,
            pivots_local_graphs,
        )