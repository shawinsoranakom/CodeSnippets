def _initialize_target_assigners(self, stride, min_box_overlap_iou):
    """Initializes the target assigners and puts them in a dictionary.

    Args:
      stride: An integer indicating the stride of the image.
      min_box_overlap_iou: float, the minimum IOU overlap that predicted boxes
        need have with groundtruth boxes to not be penalized. This is used for
        computing the class specific center heatmaps.

    Returns:
      A dictionary of initialized target assigners for each task.
    """
    target_assigners = {}
    keypoint_weights_for_center = (
        self._center_params.keypoint_weights_for_center)
    if not keypoint_weights_for_center:
      target_assigners[OBJECT_CENTER] = (
          cn_assigner.CenterNetCenterHeatmapTargetAssigner(
              stride, min_box_overlap_iou, self._compute_heatmap_sparse))
      self._center_from_keypoints = False
    else:
      # Determining the object center location by keypoint location is only
      # supported when there is exactly one keypoint prediction task and no
      # object detection task is specified.
      assert len(self._kp_params_dict) == 1 and self._od_params is None
      kp_params = next(iter(self._kp_params_dict.values()))
      # The number of keypoint_weights_for_center needs to be the same as the
      # number of keypoints.
      assert len(keypoint_weights_for_center) == len(kp_params.keypoint_indices)
      target_assigners[OBJECT_CENTER] = (
          cn_assigner.CenterNetCenterHeatmapTargetAssigner(
              stride,
              min_box_overlap_iou,
              self._compute_heatmap_sparse,
              keypoint_class_id=kp_params.class_id,
              keypoint_indices=kp_params.keypoint_indices,
              keypoint_weights_for_center=keypoint_weights_for_center))
      self._center_from_keypoints = True
    if self._od_params is not None:
      target_assigners[DETECTION_TASK] = (
          cn_assigner.CenterNetBoxTargetAssigner(stride))
    if self._kp_params_dict is not None:
      for task_name, kp_params in self._kp_params_dict.items():
        target_assigners[task_name] = (
            cn_assigner.CenterNetKeypointTargetAssigner(
                stride=stride,
                class_id=kp_params.class_id,
                keypoint_indices=kp_params.keypoint_indices,
                keypoint_std_dev=kp_params.keypoint_std_dev,
                peak_radius=kp_params.offset_peak_radius,
                per_keypoint_offset=kp_params.per_keypoint_offset,
                compute_heatmap_sparse=self._compute_heatmap_sparse,
                per_keypoint_depth=kp_params.per_keypoint_depth))
    if self._mask_params is not None:
      target_assigners[SEGMENTATION_TASK] = (
          cn_assigner.CenterNetMaskTargetAssigner(stride, boxes_scale=1.05))
    if self._densepose_params is not None:
      dp_stride = 1 if self._densepose_params.upsample_to_input_res else stride
      target_assigners[DENSEPOSE_TASK] = (
          cn_assigner.CenterNetDensePoseTargetAssigner(dp_stride))
    if self._track_params is not None:
      target_assigners[TRACK_TASK] = (
          cn_assigner.CenterNetTrackTargetAssigner(
              stride, self._track_params.num_track_ids))
    if self._temporal_offset_params is not None:
      target_assigners[TEMPORALOFFSET_TASK] = (
          cn_assigner.CenterNetTemporalOffsetTargetAssigner(stride))

    return target_assigners