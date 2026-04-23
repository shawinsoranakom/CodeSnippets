def get_default_func_arg_map(include_label_weights=True,
                             include_label_confidences=False,
                             include_multiclass_scores=False,
                             include_instance_masks=False,
                             include_instance_mask_weights=False,
                             include_keypoints=False,
                             include_keypoint_visibilities=False,
                             include_dense_pose=False,
                             include_keypoint_depths=False):
  """Returns the default mapping from a preprocessor function to its args.

  Args:
    include_label_weights: If True, preprocessing functions will modify the
      label weights, too.
    include_label_confidences: If True, preprocessing functions will modify the
      label confidences, too.
    include_multiclass_scores: If True, preprocessing functions will modify the
      multiclass scores, too.
    include_instance_masks: If True, preprocessing functions will modify the
      instance masks, too.
    include_instance_mask_weights: If True, preprocessing functions will modify
      the instance mask weights.
    include_keypoints: If True, preprocessing functions will modify the
      keypoints, too.
    include_keypoint_visibilities: If True, preprocessing functions will modify
      the keypoint visibilities, too.
    include_dense_pose: If True, preprocessing functions will modify the
      DensePose labels, too.
    include_keypoint_depths: If True, preprocessing functions will modify the
      keypoint depth labels, too.

  Returns:
    A map from preprocessing functions to the arguments they receive.
  """
  groundtruth_label_weights = None
  if include_label_weights:
    groundtruth_label_weights = (
        fields.InputDataFields.groundtruth_weights)

  groundtruth_label_confidences = None
  if include_label_confidences:
    groundtruth_label_confidences = (
        fields.InputDataFields.groundtruth_confidences)

  multiclass_scores = None
  if include_multiclass_scores:
    multiclass_scores = (fields.InputDataFields.multiclass_scores)

  groundtruth_instance_masks = None
  if include_instance_masks:
    groundtruth_instance_masks = (
        fields.InputDataFields.groundtruth_instance_masks)

  groundtruth_instance_mask_weights = None
  if include_instance_mask_weights:
    groundtruth_instance_mask_weights = (
        fields.InputDataFields.groundtruth_instance_mask_weights)

  groundtruth_keypoints = None
  if include_keypoints:
    groundtruth_keypoints = fields.InputDataFields.groundtruth_keypoints

  groundtruth_keypoint_visibilities = None
  if include_keypoint_visibilities:
    groundtruth_keypoint_visibilities = (
        fields.InputDataFields.groundtruth_keypoint_visibilities)

  groundtruth_dp_num_points = None
  groundtruth_dp_part_ids = None
  groundtruth_dp_surface_coords = None
  if include_dense_pose:
    groundtruth_dp_num_points = (
        fields.InputDataFields.groundtruth_dp_num_points)
    groundtruth_dp_part_ids = (
        fields.InputDataFields.groundtruth_dp_part_ids)
    groundtruth_dp_surface_coords = (
        fields.InputDataFields.groundtruth_dp_surface_coords)
  groundtruth_keypoint_depths = None
  groundtruth_keypoint_depth_weights = None
  if include_keypoint_depths:
    groundtruth_keypoint_depths = (
        fields.InputDataFields.groundtruth_keypoint_depths)
    groundtruth_keypoint_depth_weights = (
        fields.InputDataFields.groundtruth_keypoint_depth_weights)

  prep_func_arg_map = {
      normalize_image: (fields.InputDataFields.image,),
      random_horizontal_flip: (
          fields.InputDataFields.image,
          fields.InputDataFields.groundtruth_boxes,
          groundtruth_instance_masks,
          groundtruth_keypoints,
          groundtruth_keypoint_visibilities,
          groundtruth_dp_part_ids,
          groundtruth_dp_surface_coords,
          groundtruth_keypoint_depths,
          groundtruth_keypoint_depth_weights,
      ),
      random_vertical_flip: (
          fields.InputDataFields.image,
          fields.InputDataFields.groundtruth_boxes,
          groundtruth_instance_masks,
          groundtruth_keypoints,
      ),
      random_rotation90: (
          fields.InputDataFields.image,
          fields.InputDataFields.groundtruth_boxes,
          groundtruth_instance_masks,
          groundtruth_keypoints,
      ),
      random_pixel_value_scale: (fields.InputDataFields.image,),
      random_image_scale: (
          fields.InputDataFields.image,
          groundtruth_instance_masks,
      ),
      random_rgb_to_gray: (fields.InputDataFields.image,),
      random_adjust_brightness: (fields.InputDataFields.image,),
      random_adjust_contrast: (fields.InputDataFields.image,),
      random_adjust_hue: (fields.InputDataFields.image,),
      random_adjust_saturation: (fields.InputDataFields.image,),
      random_distort_color: (fields.InputDataFields.image,),
      random_jitter_boxes: (fields.InputDataFields.groundtruth_boxes,),
      random_crop_image:
          (fields.InputDataFields.image,
           fields.InputDataFields.groundtruth_boxes,
           fields.InputDataFields.groundtruth_classes,
           groundtruth_label_weights, groundtruth_label_confidences,
           multiclass_scores, groundtruth_instance_masks,
           groundtruth_instance_mask_weights, groundtruth_keypoints,
           groundtruth_keypoint_visibilities, groundtruth_dp_num_points,
           groundtruth_dp_part_ids, groundtruth_dp_surface_coords),
      random_pad_image:
          (fields.InputDataFields.image,
           fields.InputDataFields.groundtruth_boxes, groundtruth_instance_masks,
           groundtruth_keypoints, groundtruth_dp_surface_coords),
      random_absolute_pad_image:
          (fields.InputDataFields.image,
           fields.InputDataFields.groundtruth_boxes, groundtruth_instance_masks,
           groundtruth_keypoints, groundtruth_dp_surface_coords),
      random_crop_pad_image: (fields.InputDataFields.image,
                              fields.InputDataFields.groundtruth_boxes,
                              fields.InputDataFields.groundtruth_classes,
                              groundtruth_label_weights,
                              groundtruth_label_confidences, multiclass_scores),
      random_crop_to_aspect_ratio: (
          fields.InputDataFields.image,
          fields.InputDataFields.groundtruth_boxes,
          fields.InputDataFields.groundtruth_classes,
          groundtruth_label_weights,
          groundtruth_label_confidences,
          multiclass_scores,
          groundtruth_instance_masks,
          groundtruth_keypoints,
      ),
      random_pad_to_aspect_ratio: (
          fields.InputDataFields.image,
          fields.InputDataFields.groundtruth_boxes,
          groundtruth_instance_masks,
          groundtruth_keypoints,
      ),
      random_black_patches: (fields.InputDataFields.image,),
      random_jpeg_quality: (fields.InputDataFields.image,),
      random_downscale_to_target_pixels: (
          fields.InputDataFields.image,
          groundtruth_instance_masks,
      ),
      random_patch_gaussian: (fields.InputDataFields.image,),
      autoaugment_image: (
          fields.InputDataFields.image,
          fields.InputDataFields.groundtruth_boxes,
      ),
      retain_boxes_above_threshold: (
          fields.InputDataFields.groundtruth_boxes,
          fields.InputDataFields.groundtruth_classes,
          groundtruth_label_weights,
          groundtruth_label_confidences,
          multiclass_scores,
          groundtruth_instance_masks,
          groundtruth_keypoints,
      ),
      drop_label_probabilistically: (
          fields.InputDataFields.groundtruth_boxes,
          fields.InputDataFields.groundtruth_classes,
          groundtruth_label_weights,
          groundtruth_label_confidences,
          multiclass_scores,
          groundtruth_instance_masks,
          groundtruth_keypoints,
      ),
      remap_labels: (fields.InputDataFields.groundtruth_classes,),
      image_to_float: (fields.InputDataFields.image,),
      random_resize_method: (fields.InputDataFields.image,),
      resize_to_range: (
          fields.InputDataFields.image,
          groundtruth_instance_masks,
      ),
      resize_to_min_dimension: (
          fields.InputDataFields.image,
          groundtruth_instance_masks,
      ),
      scale_boxes_to_pixel_coordinates: (
          fields.InputDataFields.image,
          fields.InputDataFields.groundtruth_boxes,
          groundtruth_keypoints,
      ),
      resize_image: (
          fields.InputDataFields.image,
          groundtruth_instance_masks,
      ),
      subtract_channel_mean: (fields.InputDataFields.image,),
      one_hot_encoding: (fields.InputDataFields.groundtruth_image_classes,),
      rgb_to_gray: (fields.InputDataFields.image,),
      random_self_concat_image:
          (fields.InputDataFields.image,
           fields.InputDataFields.groundtruth_boxes,
           fields.InputDataFields.groundtruth_classes,
           groundtruth_label_weights, groundtruth_label_confidences,
           multiclass_scores),
      ssd_random_crop: (fields.InputDataFields.image,
                        fields.InputDataFields.groundtruth_boxes,
                        fields.InputDataFields.groundtruth_classes,
                        groundtruth_label_weights,
                        groundtruth_label_confidences, multiclass_scores,
                        groundtruth_instance_masks, groundtruth_keypoints),
      ssd_random_crop_pad: (fields.InputDataFields.image,
                            fields.InputDataFields.groundtruth_boxes,
                            fields.InputDataFields.groundtruth_classes,
                            groundtruth_label_weights,
                            groundtruth_label_confidences, multiclass_scores),
      ssd_random_crop_fixed_aspect_ratio:
          (fields.InputDataFields.image,
           fields.InputDataFields.groundtruth_boxes,
           fields.InputDataFields.groundtruth_classes,
           groundtruth_label_weights, groundtruth_label_confidences,
           multiclass_scores, groundtruth_instance_masks, groundtruth_keypoints
          ),
      ssd_random_crop_pad_fixed_aspect_ratio: (
          fields.InputDataFields.image,
          fields.InputDataFields.groundtruth_boxes,
          fields.InputDataFields.groundtruth_classes,
          groundtruth_label_weights,
          groundtruth_label_confidences,
          multiclass_scores,
          groundtruth_instance_masks,
          groundtruth_keypoints,
      ),
      convert_class_logits_to_softmax: (multiclass_scores,),
      random_square_crop_by_scale:
          (fields.InputDataFields.image,
           fields.InputDataFields.groundtruth_boxes,
           fields.InputDataFields.groundtruth_classes,
           groundtruth_label_weights, groundtruth_label_confidences,
           groundtruth_instance_masks, groundtruth_keypoints),
      random_scale_crop_and_pad_to_square:
          (fields.InputDataFields.image,
           fields.InputDataFields.groundtruth_boxes,
           fields.InputDataFields.groundtruth_classes,
           groundtruth_label_weights, groundtruth_instance_masks,
           groundtruth_keypoints, groundtruth_label_confidences),
      adjust_gamma: (fields.InputDataFields.image,),
  }

  return prep_func_arg_map