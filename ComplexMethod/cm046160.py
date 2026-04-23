def inference(self, im, bboxes=None, points=None, labels=None, masks=None):
        """Perform image segmentation inference based on the given input cues, using the currently loaded image. This
        method leverages SAM's (Segment Anything Model) architecture consisting of image encoder, prompt
        encoder, and mask decoder for real-time and promptable segmentation tasks.

        Args:
            im (torch.Tensor): The preprocessed input image in tensor format, with shape (N, C, H, W).
            bboxes (np.ndarray | list, optional): Bounding boxes with shape (N, 4), in XYXY format.
            points (np.ndarray | list, optional): Points indicating object locations with shape (N, 2), in pixels.
            labels (np.ndarray | list, optional): Labels for point prompts, shape (N, ). 1 = foreground, 0 = background.
            masks (np.ndarray, optional): Low-resolution masks from previous predictions shape (N,H,W). For SAM H=W=256.

        Returns:
            pred_masks (torch.Tensor): The output masks in shape CxHxW, where C is the number of generated masks.
            pred_scores (torch.Tensor): An array of length C containing predicted quality scores for each mask.
        """
        # Override prompts if any stored in self.prompts
        bboxes = self.prompts.pop("bboxes", bboxes)
        points = self.prompts.pop("points", points)
        masks = self.prompts.pop("masks", masks)

        frame = self.dataset.frame
        self.inference_state["im"] = im
        output_dict = self.inference_state["output_dict"]
        if len(output_dict["cond_frame_outputs"]) == 0:  # initialize prompts
            points, labels, masks = self._prepare_prompts(
                im.shape[2:], self.batch[1][0].shape[:2], bboxes, points, labels, masks
            )
            if points is not None:
                for i in range(len(points)):
                    self.add_new_prompts(obj_id=i, points=points[[i]], labels=labels[[i]], frame_idx=frame)
            elif masks is not None:
                for i in range(len(masks)):
                    self.add_new_prompts(obj_id=i, masks=masks[[i]], frame_idx=frame)
        self.propagate_in_video_preflight()

        consolidated_frame_inds = self.inference_state["consolidated_frame_inds"]
        batch_size = len(self.inference_state["obj_idx_to_id"])
        if len(output_dict["cond_frame_outputs"]) == 0:
            raise RuntimeError("No points are provided; please add points first")

        if frame in consolidated_frame_inds["cond_frame_outputs"]:
            storage_key = "cond_frame_outputs"
            current_out = output_dict[storage_key][frame]
            if self.clear_non_cond_mem_around_input and (self.clear_non_cond_mem_for_multi_obj or batch_size <= 1):
                # clear non-conditioning memory of the surrounding frames
                self._clear_non_cond_mem_around_input(frame)
        elif frame in consolidated_frame_inds["non_cond_frame_outputs"]:
            storage_key = "non_cond_frame_outputs"
            current_out = output_dict[storage_key][frame]
        else:
            storage_key = "non_cond_frame_outputs"
            current_out = self._run_single_frame_inference(
                output_dict=output_dict,
                frame_idx=frame,
                batch_size=batch_size,
                is_init_cond_frame=False,
                point_inputs=None,
                mask_inputs=None,
                reverse=False,
                run_mem_encoder=True,
            )
            output_dict[storage_key][frame] = current_out
            self._prune_non_cond_memory(frame)
        # Create slices of per-object outputs for subsequent interaction with each
        # individual object after tracking.
        self._add_output_per_object(frame, current_out, storage_key)
        self.inference_state["frames_already_tracked"].append(frame)
        pred_masks = current_out["pred_masks"].flatten(0, 1)
        pred_masks = pred_masks[(pred_masks > self.model.mask_threshold).sum((1, 2)) > 0]  # filter blank masks

        return pred_masks, torch.ones(pred_masks.shape[0], dtype=pred_masks.dtype, device=pred_masks.device)