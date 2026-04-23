def inference(
        self,
        im: torch.Tensor | np.ndarray,
        bboxes: list[list[float]] | None = None,
        masks: torch.Tensor | np.ndarray | None = None,
        points: list[list[float]] | None = None,
        labels: list[int] | None = None,
        obj_ids: list[int] | None = None,
        update_memory: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Perform inference on a single image with optional bounding boxes, masks, points and object IDs. It has two
        modes: one is to run inference on a single image without updating the memory, and the other is to update
        the memory with the provided prompts and object IDs. When update_memory is True, it will update the
        memory with the provided prompts and obj_ids. When update_memory is False, it will only run inference on
        the provided image without updating the memory.

        Args:
            im (torch.Tensor | np.ndarray): The input image tensor or numpy array.
            bboxes (list[list[float]] | None): Optional list of bounding boxes to update the memory.
            masks (torch.Tensor | np.ndarray | None): Optional masks to update the memory.
            points (list[list[float]] | None): Optional list of points to update the memory, each point is [x, y].
            labels (list[int] | None): Optional list of labels for point prompts (>0 for positive, 0 for negative).
            obj_ids (list[int] | None): Optional list of object IDs corresponding to the prompts.
            update_memory (bool): Flag to indicate whether to update the memory with new objects.

        Returns:
            res_masks (torch.Tensor): The output masks in shape (C, H, W)
            object_score_logits (torch.Tensor): Quality scores for each mask
        """
        self.get_im_features(im)
        points, labels, masks = self._prepare_prompts(
            dst_shape=self.imgsz,
            src_shape=self.batch[1][0].shape[:2],
            points=points,
            bboxes=bboxes,
            labels=labels,
            masks=masks,
        )

        if update_memory:
            if isinstance(obj_ids, int):
                obj_ids = [obj_ids]
            assert obj_ids is not None, "obj_ids must be provided when update_memory is True"
            assert masks is not None or points is not None, (
                "bboxes, masks, or points must be provided when update_memory is True"
            )
            if points is None:  # placeholder
                points = torch.zeros((len(obj_ids), 0, 2), dtype=self.torch_dtype, device=self.device)
                labels = torch.zeros((len(obj_ids), 0), dtype=torch.int32, device=self.device)
            if masks is not None:
                assert len(masks) == len(obj_ids), "masks and obj_ids must have the same length."
            assert len(points) == len(obj_ids), "points and obj_ids must have the same length."
            self.update_memory(obj_ids, points, labels, masks)

        current_out = self.track_step()
        pred_masks, pred_scores = current_out["pred_masks"], current_out["object_score_logits"]
        # filter the masks and logits based on the object indices
        if len(self.obj_idx_set) == 0:
            raise RuntimeError("No objects have been added to the state. Please add objects before inference.")
        idx = list(self.obj_idx_set)  # cls id
        pred_masks, pred_scores = pred_masks[idx], pred_scores[idx]
        # the original score are in [-32,32], and a object score larger than 0 means the object is present, we map it to [-1,1] range,
        # and use a activate function to make sure the object score logits are non-negative, so that we can use it as a mask
        pred_scores = torch.clamp_(pred_scores / 32, min=0)
        return pred_masks.flatten(0, 1), pred_scores.flatten(0, 1)