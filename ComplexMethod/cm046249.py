def __call__(self, labels: dict[str, Any]) -> dict[str, Any]:
        """Format image annotations for object detection, instance segmentation, and pose estimation tasks.

        This method standardizes the image and instance annotations to be used by the `collate_fn` in PyTorch
        DataLoader. It processes the input labels dictionary, converting annotations to the specified format and
        applying normalization if required.

        Args:
            labels (dict[str, Any]): A dictionary containing image and annotation data with the following keys:
                - 'img': The input image as a numpy array.
                - 'cls': Class labels for instances.
                - 'instances': An Instances object containing bounding boxes, segments, and keypoints.

        Returns:
            (dict[str, Any]): A dictionary with formatted data, including:
                - 'img': Formatted image tensor.
                - 'cls': Class labels tensor.
                - 'bboxes': Bounding boxes tensor in the specified format.
                - 'masks': Instance masks tensor (if return_mask is True).
                - 'keypoints': Keypoints tensor (if return_keypoint is True).
                - 'batch_idx': Batch index tensor (if batch_idx is True).

        Examples:
            >>> formatter = Format(bbox_format="xywh", normalize=True, return_mask=True)
            >>> labels = {"img": np.random.rand(640, 640, 3), "cls": np.array([0, 1]), "instances": Instances(...)}
            >>> formatted_labels = formatter(labels)
            >>> print(formatted_labels.keys())
        """
        img = labels.pop("img")
        h, w = img.shape[:2]
        cls = labels.pop("cls")
        instances = labels.pop("instances")
        instances.convert_bbox(format=self.bbox_format)
        instances.denormalize(w, h)
        nl = len(instances)

        if self.return_mask:
            if nl:
                masks, instances, cls = self._format_segments(instances, cls, w, h)
                masks = torch.from_numpy(masks)
                cls_tensor = torch.from_numpy(cls.squeeze(1))
                if self.mask_overlap:
                    sem_masks = cls_tensor[masks[0].long() - 1]  # (H, W) from (1, H, W) instance indices
                else:
                    # Create sem_masks consistent with mask_overlap=True
                    sem_masks = (masks * cls_tensor[:, None, None]).max(0).values  # (H, W) from (N, H, W) binary
                    overlap = masks.sum(dim=0) > 1  # (H, W)
                    if overlap.any():
                        weights = masks.sum(axis=(1, 2))
                        weighted_masks = masks * weights[:, None, None]  # (N, H, W)
                        weighted_masks[masks == 0] = weights.max() + 1  # handle background
                        smallest_idx = weighted_masks.argmin(dim=0)  # (H, W)
                        sem_masks[overlap] = cls_tensor[smallest_idx[overlap]]
            else:
                masks = torch.zeros(
                    1 if self.mask_overlap else nl, img.shape[0] // self.mask_ratio, img.shape[1] // self.mask_ratio
                )
                sem_masks = torch.zeros(img.shape[0] // self.mask_ratio, img.shape[1] // self.mask_ratio)
            labels["masks"] = masks
            labels["sem_masks"] = sem_masks.float()
        labels["img"] = self._format_img(img)
        labels["cls"] = torch.from_numpy(cls) if nl else torch.zeros(nl, 1)
        labels["bboxes"] = torch.from_numpy(instances.bboxes) if nl else torch.zeros((nl, 4))
        if self.return_keypoint:
            labels["keypoints"] = (
                torch.empty(0, 3) if instances.keypoints is None else torch.from_numpy(instances.keypoints)
            )
            if self.normalize:
                labels["keypoints"][..., 0] /= w
                labels["keypoints"][..., 1] /= h
        if self.return_obb:
            labels["bboxes"] = (
                xyxyxyxy2xywhr(torch.from_numpy(instances.segments)) if len(instances.segments) else torch.zeros((0, 5))
            )
        # NOTE: need to normalize obb in xywhr format for width-height consistency
        if self.normalize:
            labels["bboxes"][:, [0, 2]] /= w
            labels["bboxes"][:, [1, 3]] /= h
        # Then we can use collate_fn
        if self.batch_idx:
            labels["batch_idx"] = torch.zeros(nl)
        return labels