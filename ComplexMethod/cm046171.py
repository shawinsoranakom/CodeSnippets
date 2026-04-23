def postprocess(self, preds, img, orig_imgs):
        """Post-process the predictions to apply non-overlapping constraints if required."""
        obj_id_to_mask = preds["obj_id_to_mask"]  # low res masks
        curr_obj_ids = sorted(obj_id_to_mask.keys())
        if not isinstance(orig_imgs, list):  # input images are a torch.Tensor, not a list
            orig_imgs = ops.convert_torch2numpy_batch(orig_imgs)

        names = self.model.names if self.model.names != "visual" else {}
        if len(curr_obj_ids) == 0:
            pred_masks, pred_boxes = None, torch.zeros((0, 7), device=self.device)
        else:
            pred_masks = torch.cat([obj_id_to_mask[obj_id] for obj_id in curr_obj_ids], dim=0)
            pred_masks = F.interpolate(pred_masks.float()[None], orig_imgs[0].shape[:2], mode="bilinear")[0] > 0.5
            pred_ids = torch.tensor(curr_obj_ids, dtype=torch.int32, device=pred_masks.device)
            pred_scores = torch.tensor(
                [preds["obj_id_to_score"][obj_id] for obj_id in curr_obj_ids], device=pred_masks.device
            )
            pred_cls = torch.tensor(
                [preds["obj_id_to_cls"][obj_id] for obj_id in curr_obj_ids], device=pred_masks.device
            )
            keep = (pred_scores > self.args.conf) & pred_masks.any(dim=(1, 2))
            pred_masks = pred_masks[keep]
            pred_boxes = batched_mask_to_box(pred_masks)
            pred_boxes = torch.cat(
                [pred_boxes, pred_ids[keep][:, None], pred_scores[keep][..., None], pred_cls[keep][..., None]], dim=-1
            )
            if pred_boxes.shape[0]:
                names = names or dict(enumerate(str(i) for i in range(pred_boxes[:, 6].int().max() + 1)))
            if pred_masks.shape[0] > 1:
                tracker_scores = torch.tensor(
                    [
                        (
                            preds["obj_id_to_tracker_score"][obj_id]
                            if obj_id in preds["obj_id_to_tracker_score"]
                            else 0.0
                        )
                        for obj_id in curr_obj_ids
                    ],
                    device=pred_masks.device,
                )[keep]
                pred_masks = (
                    self._apply_object_wise_non_overlapping_constraints(
                        pred_masks.unsqueeze(1),
                        tracker_scores.unsqueeze(1),
                        background_value=0,
                    ).squeeze(1)
                ) > 0

        results = []
        for masks, boxes, orig_img, img_path in zip([pred_masks], [pred_boxes], orig_imgs, self.batch[0]):
            results.append(Results(orig_img, path=img_path, names=names, masks=masks, boxes=boxes))
        return results