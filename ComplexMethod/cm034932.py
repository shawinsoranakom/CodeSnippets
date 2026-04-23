def generate_local_graphs(self, sorted_dist_inds, gt_comp_labels):
        """Generate local graphs for GCN to predict which instance a text
        component belongs to.

        Args:
            sorted_dist_inds (ndarray): The complete graph node indices, which
                is sorted according to the Euclidean distance.
            gt_comp_labels(ndarray): The ground truth labels define the
                instance to which the text components (nodes in graphs) belong.

        Returns:
            pivot_local_graphs(list[list[int]]): The list of local graph
                neighbor indices of pivots.
            pivot_knns(list[list[int]]): The list of k-nearest neighbor indices
                of pivots.
        """

        assert sorted_dist_inds.ndim == 2
        assert (
            sorted_dist_inds.shape[0]
            == sorted_dist_inds.shape[1]
            == gt_comp_labels.shape[0]
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

            if pivot_ind < 1:
                pivot_local_graphs.append(pivot_local_graph)
                pivot_knns.append(pivot_knn)
            else:
                add_flag = True
                for graph_ind, added_knn in enumerate(pivot_knns):
                    added_pivot_ind = added_knn[0]
                    added_local_graph = pivot_local_graphs[graph_ind]

                    union = len(
                        set(pivot_local_graph[1:]).union(set(added_local_graph[1:]))
                    )
                    intersect = len(
                        set(pivot_local_graph[1:]).intersection(
                            set(added_local_graph[1:])
                        )
                    )
                    local_graph_iou = intersect / (union + 1e-8)

                    if (
                        local_graph_iou > self.local_graph_thr
                        and pivot_ind in added_knn
                        and gt_comp_labels[added_pivot_ind] == gt_comp_labels[pivot_ind]
                        and gt_comp_labels[pivot_ind] != 0
                    ):
                        add_flag = False
                        break
                if add_flag:
                    pivot_local_graphs.append(pivot_local_graph)
                    pivot_knns.append(pivot_knn)

        return pivot_local_graphs, pivot_knns