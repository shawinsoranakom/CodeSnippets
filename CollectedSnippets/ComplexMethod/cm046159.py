def _prepare_prompts(self, dst_shape, src_shape, bboxes=None, points=None, labels=None, masks=None):
        """Prepare and transform the input prompts for processing based on the destination shape.

        Args:
            dst_shape (tuple[int, int]): The target shape (height, width) for the prompts.
            src_shape (tuple[int, int]): The source shape (height, width) of the input image.
            bboxes (np.ndarray | list | None): Bounding boxes in XYXY format with shape (N, 4).
            points (np.ndarray | list | None): Points indicating object locations with shape (N, 2) or (N, num_points,
                2), in pixels.
            labels (np.ndarray | list | None): Point prompt labels with shape (N) or (N, num_points). 1 for foreground,
                0 for background.
            masks (list[np.ndarray] | np.ndarray | None): Masks for the objects, where each mask is a 2D array with
                shape (H, W).

        Returns:
            bboxes (torch.Tensor | None): Transformed bounding boxes.
            points (torch.Tensor | None): Transformed points.
            labels (torch.Tensor | None): Transformed labels.
            masks (torch.Tensor | None): Transformed masks.

        Raises:
            AssertionError: If the number of points don't match the number of labels, in case labels were passed.
        """
        r = 1.0 if self.segment_all else min(dst_shape[0] / src_shape[0], dst_shape[1] / src_shape[1])
        # Transform input prompts
        if points is not None:
            points = torch.as_tensor(points, dtype=self.torch_dtype, device=self.device)
            points = points[None] if points.ndim == 1 else points
            # Assuming labels are all positive if users don't pass labels.
            if labels is None:
                labels = np.ones(points.shape[:-1])
            labels = torch.as_tensor(labels, dtype=torch.int32, device=self.device)
            assert points.shape[-2] == labels.shape[-1], (
                f"Number of points {points.shape[-2]} should match number of labels {labels.shape[-1]}."
            )
            points *= r
            if points.ndim == 2:
                # (N, 2) --> (N, 1, 2), (N, ) --> (N, 1)
                points, labels = points[:, None, :], labels[:, None]
        if bboxes is not None:
            bboxes = torch.as_tensor(bboxes, dtype=self.torch_dtype, device=self.device)
            bboxes = bboxes[None] if bboxes.ndim == 1 else bboxes
            bboxes *= r
        if masks is not None:
            masks = np.asarray(masks, dtype=np.uint8)
            masks = masks[None] if masks.ndim == 2 else masks
            letterbox = LetterBox(dst_shape, auto=False, center=False, padding_value=0, interpolation=cv2.INTER_NEAREST)
            masks = np.stack([letterbox(image=x).squeeze() for x in masks], axis=0)
            masks = torch.tensor(masks, dtype=self.torch_dtype, device=self.device)
        return bboxes, points, labels, masks