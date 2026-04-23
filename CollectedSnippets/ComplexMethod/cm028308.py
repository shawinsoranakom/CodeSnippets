def provide_groundtruth(
      self,
      groundtruth_boxes_list,
      groundtruth_classes_list,
      groundtruth_masks_list=None,
      groundtruth_mask_weights_list=None,
      groundtruth_keypoints_list=None,
      groundtruth_keypoint_visibilities_list=None,
      groundtruth_dp_num_points_list=None,
      groundtruth_dp_part_ids_list=None,
      groundtruth_dp_surface_coords_list=None,
      groundtruth_track_ids_list=None,
      groundtruth_temporal_offsets_list=None,
      groundtruth_track_match_flags_list=None,
      groundtruth_weights_list=None,
      groundtruth_confidences_list=None,
      groundtruth_is_crowd_list=None,
      groundtruth_group_of_list=None,
      groundtruth_area_list=None,
      is_annotated_list=None,
      groundtruth_labeled_classes=None,
      groundtruth_verified_neg_classes=None,
      groundtruth_not_exhaustive_classes=None,
      groundtruth_keypoint_depths_list=None,
      groundtruth_keypoint_depth_weights_list=None,
      groundtruth_image_classes=None,
      training_step=None):
    """Provide groundtruth tensors.

    Args:
      groundtruth_boxes_list: a list of 2-D tf.float32 tensors of shape
        [num_boxes, 4] containing coordinates of the groundtruth boxes.
          Groundtruth boxes are provided in [y_min, x_min, y_max, x_max]
          format and assumed to be normalized and clipped
          relative to the image window with y_min <= y_max and x_min <= x_max.
      groundtruth_classes_list: a list of 2-D tf.float32 one-hot (or k-hot)
        tensors of shape [num_boxes, num_classes] containing the class targets
        with the 0th index assumed to map to the first non-background class.
      groundtruth_masks_list: a list of 3-D tf.float32 tensors of
        shape [num_boxes, height_in, width_in] containing instance
        masks with values in {0, 1}.  If None, no masks are provided.
        Mask resolution `height_in`x`width_in` must agree with the resolution
        of the input image tensor provided to the `preprocess` function.
      groundtruth_mask_weights_list: a list of 1-D tf.float32 tensors of shape
        [num_boxes] with weights for each instance mask.
      groundtruth_keypoints_list: a list of 3-D tf.float32 tensors of
        shape [num_boxes, num_keypoints, 2] containing keypoints.
        Keypoints are assumed to be provided in normalized coordinates and
        missing keypoints should be encoded as NaN (but it is recommended to use
        `groundtruth_keypoint_visibilities_list`).
      groundtruth_keypoint_visibilities_list: a list of 3-D tf.bool tensors
        of shape [num_boxes, num_keypoints] containing keypoint visibilities.
      groundtruth_dp_num_points_list: a list of 1-D tf.int32 tensors of shape
        [num_boxes] containing the number of DensePose sampled points.
      groundtruth_dp_part_ids_list: a list of 2-D tf.int32 tensors of shape
        [num_boxes, max_sampled_points] containing the DensePose part ids
        (0-indexed) for each sampled point. Note that there may be padding.
      groundtruth_dp_surface_coords_list: a list of 3-D tf.float32 tensors of
        shape [num_boxes, max_sampled_points, 4] containing the DensePose
        surface coordinates for each sampled point. Note that there may be
        padding.
      groundtruth_track_ids_list: a list of 1-D tf.int32 tensors of shape
        [num_boxes] containing the track IDs of groundtruth objects.
      groundtruth_temporal_offsets_list: a list of 2-D tf.float32 tensors
        of shape [num_boxes, 2] containing the spatial offsets of objects'
        centers compared with the previous frame.
      groundtruth_track_match_flags_list: a list of 1-D tf.float32 tensors
        of shape [num_boxes] containing 0-1 flags that indicate if an object
        has existed in the previous frame.
      groundtruth_weights_list: A list of 1-D tf.float32 tensors of shape
        [num_boxes] containing weights for groundtruth boxes.
      groundtruth_confidences_list: A list of 2-D tf.float32 tensors of shape
        [num_boxes, num_classes] containing class confidences for groundtruth
        boxes.
      groundtruth_is_crowd_list: A list of 1-D tf.bool tensors of shape
        [num_boxes] containing is_crowd annotations.
      groundtruth_group_of_list: A list of 1-D tf.bool tensors of shape
        [num_boxes] containing group_of annotations.
      groundtruth_area_list: A list of 1-D tf.float32 tensors of shape
        [num_boxes] containing the area (in the original absolute coordinates)
        of the annotations.
      is_annotated_list: A list of scalar tf.bool tensors indicating whether
        images have been labeled or not.
      groundtruth_labeled_classes: A list of 1-D tf.float32 tensors of shape
        [num_classes], containing label indices encoded as k-hot of the classes
        that are exhaustively annotated.
      groundtruth_verified_neg_classes: A list of 1-D tf.float32 tensors of
        shape [num_classes], containing a K-hot representation of classes
        which were verified as not present in the image.
      groundtruth_not_exhaustive_classes: A list of 1-D tf.float32 tensors of
        shape [num_classes], containing a K-hot representation of classes
        which don't have all of their instances marked exhaustively.
      groundtruth_keypoint_depths_list: a list of 2-D tf.float32 tensors
        of shape [num_boxes, num_keypoints] containing keypoint relative depths.
      groundtruth_keypoint_depth_weights_list: a list of 2-D tf.float32 tensors
        of shape [num_boxes, num_keypoints] containing the weights of the
        relative depths.
      groundtruth_image_classes: A list of 1-D tf.float32 tensors of shape
        [num_classes], containing label indices encoded as k-hot of the classes
        that are present or not present in the image.
      training_step: An integer denoting the current training step. This is
        useful when models want to anneal loss terms.
    """
    self._groundtruth_lists[fields.BoxListFields.boxes] = groundtruth_boxes_list
    self._groundtruth_lists[
        fields.BoxListFields.classes] = groundtruth_classes_list
    if groundtruth_weights_list:
      self._groundtruth_lists[fields.BoxListFields.
                              weights] = groundtruth_weights_list
    if groundtruth_confidences_list:
      self._groundtruth_lists[fields.BoxListFields.
                              confidences] = groundtruth_confidences_list
    if groundtruth_masks_list:
      self._groundtruth_lists[
          fields.BoxListFields.masks] = groundtruth_masks_list
    if groundtruth_mask_weights_list:
      self._groundtruth_lists[
          fields.BoxListFields.mask_weights] = groundtruth_mask_weights_list
    if groundtruth_keypoints_list:
      self._groundtruth_lists[
          fields.BoxListFields.keypoints] = groundtruth_keypoints_list
    if groundtruth_keypoint_visibilities_list:
      self._groundtruth_lists[
          fields.BoxListFields.keypoint_visibilities] = (
              groundtruth_keypoint_visibilities_list)
    if groundtruth_keypoint_depths_list:
      self._groundtruth_lists[
          fields.BoxListFields.keypoint_depths] = (
              groundtruth_keypoint_depths_list)
    if groundtruth_keypoint_depth_weights_list:
      self._groundtruth_lists[
          fields.BoxListFields.keypoint_depth_weights] = (
              groundtruth_keypoint_depth_weights_list)
    if groundtruth_dp_num_points_list:
      self._groundtruth_lists[
          fields.BoxListFields.densepose_num_points] = (
              groundtruth_dp_num_points_list)
    if groundtruth_dp_part_ids_list:
      self._groundtruth_lists[
          fields.BoxListFields.densepose_part_ids] = (
              groundtruth_dp_part_ids_list)
    if groundtruth_dp_surface_coords_list:
      self._groundtruth_lists[
          fields.BoxListFields.densepose_surface_coords] = (
              groundtruth_dp_surface_coords_list)
    if groundtruth_track_ids_list:
      self._groundtruth_lists[
          fields.BoxListFields.track_ids] = groundtruth_track_ids_list
    if groundtruth_temporal_offsets_list:
      self._groundtruth_lists[
          fields.BoxListFields.temporal_offsets] = (
              groundtruth_temporal_offsets_list)
    if groundtruth_track_match_flags_list:
      self._groundtruth_lists[
          fields.BoxListFields.track_match_flags] = (
              groundtruth_track_match_flags_list)
    if groundtruth_is_crowd_list:
      self._groundtruth_lists[
          fields.BoxListFields.is_crowd] = groundtruth_is_crowd_list
    if groundtruth_group_of_list:
      self._groundtruth_lists[
          fields.BoxListFields.group_of] = groundtruth_group_of_list
    if groundtruth_area_list:
      self._groundtruth_lists[
          fields.InputDataFields.groundtruth_area] = groundtruth_area_list
    if is_annotated_list:
      self._groundtruth_lists[
          fields.InputDataFields.is_annotated] = is_annotated_list
    if groundtruth_labeled_classes:
      self._groundtruth_lists[
          fields.InputDataFields
          .groundtruth_labeled_classes] = groundtruth_labeled_classes
    if groundtruth_verified_neg_classes:
      self._groundtruth_lists[
          fields.InputDataFields
          .groundtruth_verified_neg_classes] = groundtruth_verified_neg_classes
    if groundtruth_image_classes:
      self._groundtruth_lists[
          fields.InputDataFields
          .groundtruth_image_classes] = groundtruth_image_classes
    if groundtruth_not_exhaustive_classes:
      self._groundtruth_lists[
          fields.InputDataFields
          .groundtruth_not_exhaustive_classes] = (
              groundtruth_not_exhaustive_classes)
    if training_step is not None:
      self._training_step = training_step