def provide_groundtruth(model, labels, training_step=None):
  """Provides the labels to a model as groundtruth.

  This helper function extracts the corresponding boxes, classes,
  keypoints, weights, masks, etc. from the labels, and provides it
  as groundtruth to the models.

  Args:
    model: The detection model to provide groundtruth to.
    labels: The labels for the training or evaluation inputs.
    training_step: int, optional. The training step for the model. Useful for
      models which want to anneal loss weights.
  """
  gt_boxes_list = labels[fields.InputDataFields.groundtruth_boxes]
  gt_classes_list = labels[fields.InputDataFields.groundtruth_classes]
  gt_masks_list = None
  if fields.InputDataFields.groundtruth_instance_masks in labels:
    gt_masks_list = labels[fields.InputDataFields.groundtruth_instance_masks]
  gt_mask_weights_list = None
  if fields.InputDataFields.groundtruth_instance_mask_weights in labels:
    gt_mask_weights_list = labels[
        fields.InputDataFields.groundtruth_instance_mask_weights]
  gt_keypoints_list = None
  if fields.InputDataFields.groundtruth_keypoints in labels:
    gt_keypoints_list = labels[fields.InputDataFields.groundtruth_keypoints]
  gt_keypoint_depths_list = None
  gt_keypoint_depth_weights_list = None
  if fields.InputDataFields.groundtruth_keypoint_depths in labels:
    gt_keypoint_depths_list = (
        labels[fields.InputDataFields.groundtruth_keypoint_depths])
    gt_keypoint_depth_weights_list = (
        labels[fields.InputDataFields.groundtruth_keypoint_depth_weights])
  gt_keypoint_visibilities_list = None
  if fields.InputDataFields.groundtruth_keypoint_visibilities in labels:
    gt_keypoint_visibilities_list = labels[
        fields.InputDataFields.groundtruth_keypoint_visibilities]
  gt_dp_num_points_list = None
  if fields.InputDataFields.groundtruth_dp_num_points in labels:
    gt_dp_num_points_list = labels[
        fields.InputDataFields.groundtruth_dp_num_points]
  gt_dp_part_ids_list = None
  if fields.InputDataFields.groundtruth_dp_part_ids in labels:
    gt_dp_part_ids_list = labels[fields.InputDataFields.groundtruth_dp_part_ids]
  gt_dp_surface_coords_list = None
  if fields.InputDataFields.groundtruth_dp_surface_coords in labels:
    gt_dp_surface_coords_list = labels[
        fields.InputDataFields.groundtruth_dp_surface_coords]
  gt_track_ids_list = None
  if fields.InputDataFields.groundtruth_track_ids in labels:
    gt_track_ids_list = labels[fields.InputDataFields.groundtruth_track_ids]
  gt_weights_list = None
  if fields.InputDataFields.groundtruth_weights in labels:
    gt_weights_list = labels[fields.InputDataFields.groundtruth_weights]
  gt_confidences_list = None
  if fields.InputDataFields.groundtruth_confidences in labels:
    gt_confidences_list = labels[fields.InputDataFields.groundtruth_confidences]
  gt_is_crowd_list = None
  if fields.InputDataFields.groundtruth_is_crowd in labels:
    gt_is_crowd_list = labels[fields.InputDataFields.groundtruth_is_crowd]
  gt_group_of_list = None
  if fields.InputDataFields.groundtruth_group_of in labels:
    gt_group_of_list = labels[fields.InputDataFields.groundtruth_group_of]
  gt_area_list = None
  if fields.InputDataFields.groundtruth_area in labels:
    gt_area_list = labels[fields.InputDataFields.groundtruth_area]
  gt_labeled_classes = None
  if fields.InputDataFields.groundtruth_labeled_classes in labels:
    gt_labeled_classes = labels[
        fields.InputDataFields.groundtruth_labeled_classes]
  gt_verified_neg_classes = None
  if fields.InputDataFields.groundtruth_verified_neg_classes in labels:
    gt_verified_neg_classes = labels[
        fields.InputDataFields.groundtruth_verified_neg_classes]
  gt_not_exhaustive_classes = None
  if fields.InputDataFields.groundtruth_not_exhaustive_classes in labels:
    gt_not_exhaustive_classes = labels[
        fields.InputDataFields.groundtruth_not_exhaustive_classes]
  groundtruth_image_classes = None
  if fields.InputDataFields.groundtruth_image_classes in labels:
    groundtruth_image_classes = labels[
        fields.InputDataFields.groundtruth_image_classes]
  model.provide_groundtruth(
      groundtruth_boxes_list=gt_boxes_list,
      groundtruth_classes_list=gt_classes_list,
      groundtruth_confidences_list=gt_confidences_list,
      groundtruth_labeled_classes=gt_labeled_classes,
      groundtruth_masks_list=gt_masks_list,
      groundtruth_mask_weights_list=gt_mask_weights_list,
      groundtruth_keypoints_list=gt_keypoints_list,
      groundtruth_keypoint_visibilities_list=gt_keypoint_visibilities_list,
      groundtruth_dp_num_points_list=gt_dp_num_points_list,
      groundtruth_dp_part_ids_list=gt_dp_part_ids_list,
      groundtruth_dp_surface_coords_list=gt_dp_surface_coords_list,
      groundtruth_weights_list=gt_weights_list,
      groundtruth_is_crowd_list=gt_is_crowd_list,
      groundtruth_group_of_list=gt_group_of_list,
      groundtruth_area_list=gt_area_list,
      groundtruth_track_ids_list=gt_track_ids_list,
      groundtruth_verified_neg_classes=gt_verified_neg_classes,
      groundtruth_not_exhaustive_classes=gt_not_exhaustive_classes,
      groundtruth_keypoint_depths_list=gt_keypoint_depths_list,
      groundtruth_keypoint_depth_weights_list=gt_keypoint_depth_weights_list,
      groundtruth_image_classes=groundtruth_image_classes,
      training_step=training_step)