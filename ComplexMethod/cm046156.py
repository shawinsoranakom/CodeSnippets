def prompt(self, results, bboxes=None, points=None, labels=None, texts=None):
        """Perform image segmentation inference based on cues like bounding boxes, points, and text prompts.

        Args:
            results (Results | list[Results]): Original inference results from FastSAM models without any prompts.
            bboxes (np.ndarray | list, optional): Bounding boxes with shape (N, 4), in XYXY format.
            points (np.ndarray | list, optional): Points indicating object locations with shape (N, 2), in pixels.
            labels (np.ndarray | list, optional): Labels for point prompts, shape (N, ). 1 = foreground, 0 = background.
            texts (str | list[str], optional): Textual prompts, a list containing string objects.

        Returns:
            (list[Results]): Output results filtered and determined by the provided prompts.
        """
        if bboxes is None and points is None and texts is None:
            return results
        prompt_results = []
        if not isinstance(results, list):
            results = [results]
        for result in results:
            if len(result) == 0:
                prompt_results.append(result)
                continue
            masks = result.masks.data
            if masks.shape[1:] != result.orig_shape:
                masks = (scale_masks(masks[None].float(), result.orig_shape)[0] > 0.5).byte()
            # bboxes prompt
            idx = torch.zeros(len(result), dtype=torch.bool, device=self.device)
            if bboxes is not None:
                bboxes = torch.as_tensor(bboxes, dtype=torch.int32, device=self.device)
                bboxes = bboxes[None] if bboxes.ndim == 1 else bboxes
                bbox_areas = (bboxes[:, 3] - bboxes[:, 1]) * (bboxes[:, 2] - bboxes[:, 0])
                mask_areas = torch.stack([masks[:, b[1] : b[3], b[0] : b[2]].sum(dim=(1, 2)) for b in bboxes])
                full_mask_areas = torch.sum(masks, dim=(1, 2))

                union = bbox_areas[:, None] + full_mask_areas - mask_areas
                idx[torch.argmax(mask_areas / union, dim=1)] = True
            if points is not None:
                points = torch.as_tensor(points, dtype=torch.int32, device=self.device)
                points = points[None] if points.ndim == 1 else points
                if labels is None:
                    labels = torch.ones(points.shape[0])
                labels = torch.as_tensor(labels, dtype=torch.int32, device=self.device)
                assert len(labels) == len(points), (
                    f"Expected `labels` to have the same length as `points`, but got {len(labels)} and {len(points)}."
                )
                point_idx = (
                    torch.ones(len(result), dtype=torch.bool, device=self.device)
                    if labels.sum() == 0  # all negative points
                    else torch.zeros(len(result), dtype=torch.bool, device=self.device)
                )
                for point, label in zip(points, labels):
                    point_idx[torch.nonzero(masks[:, point[1], point[0]], as_tuple=True)[0]] = bool(label)
                idx |= point_idx
            if texts is not None:
                if isinstance(texts, str):
                    texts = [texts]
                crop_ims, filter_idx = [], []
                for i, b in enumerate(result.boxes.xyxy.tolist()):
                    x1, y1, x2, y2 = (int(x) for x in b)
                    if (masks[i].sum() if TORCH_1_10 else masks[i].sum(0).sum()) <= 100:  # torch 1.9 bug workaround
                        filter_idx.append(i)
                        continue
                    crop = result.orig_img[y1:y2, x1:x2] * masks[i, y1:y2, x1:x2, None].cpu().numpy()
                    crop_ims.append(Image.fromarray(crop[:, :, ::-1]))
                similarity = self._clip_inference(crop_ims, texts)
                text_idx = torch.argmax(similarity, dim=-1)  # (M, )
                if len(filter_idx):
                    # Remap text_idx to its original index before filter
                    ori_idxs = [i for i in range(len(result)) if i not in filter_idx]
                    text_idx = torch.tensor(ori_idxs[int(text_idx)], device=self.device)
                idx[text_idx] = True

            prompt_results.append(result[idx])

        return prompt_results