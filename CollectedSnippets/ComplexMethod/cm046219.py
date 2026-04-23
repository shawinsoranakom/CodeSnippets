def forward(
        self,
        pred_bboxes: torch.Tensor,
        pred_scores: torch.Tensor,
        gt_bboxes: torch.Tensor,
        gt_cls: torch.Tensor,
        gt_groups: list[int],
        masks: torch.Tensor | None = None,
        gt_mask: list[torch.Tensor] | None = None,
    ) -> list[tuple[torch.Tensor, torch.Tensor]]:
        """Compute optimal assignment between predictions and ground truth using Hungarian algorithm.

        This method calculates matching costs based on classification scores, bounding box coordinates, and optionally
        mask predictions, then finds the optimal bipartite assignment between predictions and ground truth.

        Args:
            pred_bboxes (torch.Tensor): Predicted bounding boxes with shape (batch_size, num_queries, 4).
            pred_scores (torch.Tensor): Predicted classification scores with shape (batch_size, num_queries,
                num_classes).
            gt_bboxes (torch.Tensor): Ground truth bounding boxes with shape (num_gts, 4).
            gt_cls (torch.Tensor): Ground truth class labels with shape (num_gts,).
            gt_groups (list[int]): Number of ground truth boxes for each image in the batch.
            masks (torch.Tensor, optional): Predicted masks with shape (batch_size, num_queries, height, width).
            gt_mask (list[torch.Tensor], optional): Ground truth masks, each with shape (num_masks, Height, Width).

        Returns:
            (list[tuple[torch.Tensor, torch.Tensor]]): A list of size batch_size, each element is a tuple (index_i,
                index_j), where index_i is the tensor of indices of the selected predictions (in order) and index_j is
                the tensor of indices of the corresponding selected ground truth targets (in order).
            For each batch element, it holds: len(index_i) = len(index_j) = min(num_queries, num_target_boxes).
        """
        bs, nq, nc = pred_scores.shape

        if sum(gt_groups) == 0:
            return [(torch.tensor([], dtype=torch.long), torch.tensor([], dtype=torch.long)) for _ in range(bs)]

        # Flatten to compute cost matrices in batch format
        pred_scores = pred_scores.detach().view(-1, nc)
        pred_scores = F.sigmoid(pred_scores) if self.use_fl else F.softmax(pred_scores, dim=-1)
        pred_bboxes = pred_bboxes.detach().view(-1, 4)

        # Compute classification cost
        pred_scores = pred_scores[:, gt_cls]
        if self.use_fl:
            neg_cost_class = (1 - self.alpha) * (pred_scores**self.gamma) * (-(1 - pred_scores + 1e-8).log())
            pos_cost_class = self.alpha * ((1 - pred_scores) ** self.gamma) * (-(pred_scores + 1e-8).log())
            cost_class = pos_cost_class - neg_cost_class
        else:
            cost_class = -pred_scores

        # Compute L1 cost between boxes
        cost_bbox = (pred_bboxes.unsqueeze(1) - gt_bboxes.unsqueeze(0)).abs().sum(-1)  # (bs*num_queries, num_gt)

        # Compute GIoU cost between boxes, (bs*num_queries, num_gt)
        cost_giou = 1.0 - bbox_iou(pred_bboxes.unsqueeze(1), gt_bboxes.unsqueeze(0), xywh=True, GIoU=True).squeeze(-1)

        # Combine costs into final cost matrix
        C = (
            self.cost_gain["class"] * cost_class
            + self.cost_gain["bbox"] * cost_bbox
            + self.cost_gain["giou"] * cost_giou
        )

        # Add mask costs if available
        if self.with_mask:
            C += self._cost_mask(bs, gt_groups, masks, gt_mask)

        # Set invalid values (NaNs and infinities) to 0
        C[C.isnan() | C.isinf()] = 0.0

        C = C.view(bs, nq, -1).cpu()
        indices = [linear_sum_assignment(c[i]) for i, c in enumerate(C.split(gt_groups, -1))]
        gt_groups = torch.as_tensor([0, *gt_groups[:-1]]).cumsum_(0)  # (idx for queries, idx for gt)
        return [
            (torch.tensor(i, dtype=torch.long), torch.tensor(j, dtype=torch.long) + gt_groups[k])
            for k, (i, j) in enumerate(indices)
        ]