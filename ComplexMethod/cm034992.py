def __call__(self, preds, shape_list):
        """
        Args:
            edges (ndarray): The edge array of shape N * 2, each row is a node
                index pair that makes up an edge in graph.
            scores (ndarray): The edge score array of shape (N,).
            text_comps (ndarray): The text components.

        Returns:
            List[list[float]]: The predicted boundaries of text instances.
        """
        edges, scores, text_comps = preds
        if edges is not None:
            if isinstance(edges, paddle.Tensor):
                edges = edges.numpy()
            if isinstance(scores, paddle.Tensor):
                scores = scores.numpy()
            if isinstance(text_comps, paddle.Tensor):
                text_comps = text_comps.numpy()
            assert len(edges) == len(scores)
            assert text_comps.ndim == 2
            assert text_comps.shape[1] == 9

            vertices, score_dict = graph_propagation(edges, scores, text_comps)
            clusters = connected_components(vertices, score_dict, self.link_thr)
            pred_labels = clusters2labels(clusters, text_comps.shape[0])
            text_comps, pred_labels = remove_single(text_comps, pred_labels)
            boundaries = comps2boundaries(text_comps, pred_labels)
        else:
            boundaries = []

        boundaries, scores = self.resize_boundary(
            boundaries, (1 / shape_list[0, 2:]).tolist()[::-1]
        )
        boxes_batch = [dict(points=boundaries, scores=scores)]
        return boxes_batch