def forward(self, outputs, targets, group_detr):
        """
        Differences:
        - out_prob = outputs["logits"].flatten(0, 1).sigmoid() instead of softmax
        - class_cost uses alpha and gamma
        """
        batch_size, num_queries = outputs["logits"].shape[:2]

        # We flatten to compute the cost matrices in a batch
        out_prob = outputs["logits"].flatten(0, 1).sigmoid()  # [batch_size * num_queries, num_classes]
        out_bbox = outputs["pred_boxes"].flatten(0, 1)  # [batch_size * num_queries, 4]

        # Also concat the target labels and boxes
        target_ids = torch.cat([v["class_labels"] for v in targets])
        target_bbox = torch.cat([v["boxes"] for v in targets])

        # Compute the classification cost.
        alpha = 0.25
        gamma = 2.0
        neg_cost_class = (1 - alpha) * (out_prob**gamma) * (-(1 - out_prob + 1e-8).log())
        pos_cost_class = alpha * ((1 - out_prob) ** gamma) * (-(out_prob + 1e-8).log())
        class_cost = pos_cost_class[:, target_ids] - neg_cost_class[:, target_ids]

        # Compute the L1 cost between boxes, cdist only supports float32
        dtype = out_bbox.dtype
        out_bbox = out_bbox.to(torch.float32)
        target_bbox = target_bbox.to(torch.float32)
        bbox_cost = torch.cdist(out_bbox, target_bbox, p=1)
        bbox_cost = bbox_cost.to(dtype)

        # Compute the giou cost between boxes
        giou_cost = -generalized_box_iou(center_to_corners_format(out_bbox), center_to_corners_format(target_bbox))

        # Final cost matrix
        cost_matrix = self.bbox_cost * bbox_cost + self.class_cost * class_cost + self.giou_cost * giou_cost
        cost_matrix = cost_matrix.view(batch_size, num_queries, -1).cpu()

        sizes = [len(v["boxes"]) for v in targets]
        indices = []
        group_num_queries = num_queries // group_detr
        cost_matrix_list = cost_matrix.split(group_num_queries, dim=1)
        for group_id in range(group_detr):
            group_cost_matrix = cost_matrix_list[group_id]
            group_indices = [linear_sum_assignment(c[i]) for i, c in enumerate(group_cost_matrix.split(sizes, -1))]
            if group_id == 0:
                indices = group_indices
            else:
                indices = [
                    (
                        np.concatenate([indice1[0], indice2[0] + group_num_queries * group_id]),
                        np.concatenate([indice1[1], indice2[1]]),
                    )
                    for indice1, indice2 in zip(indices, group_indices)
                ]
        return [(torch.as_tensor(i, dtype=torch.int64), torch.as_tensor(j, dtype=torch.int64)) for i, j in indices]