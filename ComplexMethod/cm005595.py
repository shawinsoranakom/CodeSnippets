def _sanitize_parameters(self, **kwargs):
        preprocess_kwargs = {}
        postprocess_kwargs = {}
        forward_params = {}
        # preprocess args
        if "points_per_batch" in kwargs:
            preprocess_kwargs["points_per_batch"] = kwargs["points_per_batch"]
        if "points_per_crop" in kwargs:
            preprocess_kwargs["points_per_crop"] = kwargs["points_per_crop"]
        if "crops_n_layers" in kwargs:
            preprocess_kwargs["crops_n_layers"] = kwargs["crops_n_layers"]
        if "crop_overlap_ratio" in kwargs:
            preprocess_kwargs["crop_overlap_ratio"] = kwargs["crop_overlap_ratio"]
        if "crop_n_points_downscale_factor" in kwargs:
            preprocess_kwargs["crop_n_points_downscale_factor"] = kwargs["crop_n_points_downscale_factor"]
        if "timeout" in kwargs:
            preprocess_kwargs["timeout"] = kwargs["timeout"]
        # postprocess args
        if "pred_iou_thresh" in kwargs:
            forward_params["pred_iou_thresh"] = kwargs["pred_iou_thresh"]
        if "stability_score_offset" in kwargs:
            forward_params["stability_score_offset"] = kwargs["stability_score_offset"]
        if "mask_threshold" in kwargs:
            forward_params["mask_threshold"] = kwargs["mask_threshold"]
        if "stability_score_thresh" in kwargs:
            forward_params["stability_score_thresh"] = kwargs["stability_score_thresh"]
        if "max_hole_area" in kwargs:
            forward_params["max_hole_area"] = kwargs["max_hole_area"]
        if "max_sprinkle_area" in kwargs:
            forward_params["max_sprinkle_area"] = kwargs["max_sprinkle_area"]
        if "crops_nms_thresh" in kwargs:
            postprocess_kwargs["crops_nms_thresh"] = kwargs["crops_nms_thresh"]
        if "output_rle_mask" in kwargs:
            postprocess_kwargs["output_rle_mask"] = kwargs["output_rle_mask"]
        if "output_bboxes_mask" in kwargs:
            postprocess_kwargs["output_bboxes_mask"] = kwargs["output_bboxes_mask"]
        return preprocess_kwargs, forward_params, postprocess_kwargs