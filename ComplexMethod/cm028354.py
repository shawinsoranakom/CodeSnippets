def draw_side_by_side_evaluation_image(eval_dict,
                                       category_index,
                                       max_boxes_to_draw=20,
                                       min_score_thresh=0.2,
                                       use_normalized_coordinates=True,
                                       keypoint_edges=None):
  """Creates a side-by-side image with detections and groundtruth.

  Bounding boxes (and instance masks, if available) are visualized on both
  subimages.

  Args:
    eval_dict: The evaluation dictionary returned by
      eval_util.result_dict_for_batched_example() or
      eval_util.result_dict_for_single_example().
    category_index: A category index (dictionary) produced from a labelmap.
    max_boxes_to_draw: The maximum number of boxes to draw for detections.
    min_score_thresh: The minimum score threshold for showing detections.
    use_normalized_coordinates: Whether to assume boxes and keypoints are in
      normalized coordinates (as opposed to absolute coordinates).
      Default is True.
    keypoint_edges: A list of tuples with keypoint indices that specify which
      keypoints should be connected by an edge, e.g. [(0, 1), (2, 4)] draws
      edges from keypoint 0 to 1 and from keypoint 2 to 4.

  Returns:
    A list of [1, H, 2 * W, C] uint8 tensor. The subimage on the left
      corresponds to detections, while the subimage on the right corresponds to
      groundtruth.
  """
  detection_fields = fields.DetectionResultFields()
  input_data_fields = fields.InputDataFields()

  images_with_detections_list = []

  # Add the batch dimension if the eval_dict is for single example.
  if len(eval_dict[detection_fields.detection_classes].shape) == 1:
    for key in eval_dict:
      if (key != input_data_fields.original_image and
          key != input_data_fields.image_additional_channels):
        eval_dict[key] = tf.expand_dims(eval_dict[key], 0)

  num_gt_boxes = [-1] * eval_dict[input_data_fields.original_image].shape[0]
  if input_data_fields.num_groundtruth_boxes in eval_dict:
    num_gt_boxes = tf.cast(eval_dict[input_data_fields.num_groundtruth_boxes],
                           tf.int32)
  for indx in range(eval_dict[input_data_fields.original_image].shape[0]):
    instance_masks = None
    if detection_fields.detection_masks in eval_dict:
      instance_masks = tf.cast(
          tf.expand_dims(
              eval_dict[detection_fields.detection_masks][indx], axis=0),
          tf.uint8)
    keypoints = None
    keypoint_scores = None
    if detection_fields.detection_keypoints in eval_dict:
      keypoints = tf.expand_dims(
          eval_dict[detection_fields.detection_keypoints][indx], axis=0)
      if detection_fields.detection_keypoint_scores in eval_dict:
        keypoint_scores = tf.expand_dims(
            eval_dict[detection_fields.detection_keypoint_scores][indx], axis=0)
      else:
        keypoint_scores = tf.expand_dims(tf.cast(
            keypoint_ops.set_keypoint_visibilities(
                eval_dict[detection_fields.detection_keypoints][indx]),
            dtype=tf.float32), axis=0)

    groundtruth_instance_masks = None
    if input_data_fields.groundtruth_instance_masks in eval_dict:
      groundtruth_instance_masks = tf.cast(
          tf.expand_dims(
              eval_dict[input_data_fields.groundtruth_instance_masks][indx],
              axis=0), tf.uint8)
    groundtruth_keypoints = None
    groundtruth_keypoint_scores = None
    gt_kpt_vis_fld = input_data_fields.groundtruth_keypoint_visibilities
    if input_data_fields.groundtruth_keypoints in eval_dict:
      groundtruth_keypoints = tf.expand_dims(
          eval_dict[input_data_fields.groundtruth_keypoints][indx], axis=0)
      if gt_kpt_vis_fld in eval_dict:
        groundtruth_keypoint_scores = tf.expand_dims(
            tf.cast(eval_dict[gt_kpt_vis_fld][indx], dtype=tf.float32), axis=0)
      else:
        groundtruth_keypoint_scores = tf.expand_dims(tf.cast(
            keypoint_ops.set_keypoint_visibilities(
                eval_dict[input_data_fields.groundtruth_keypoints][indx]),
            dtype=tf.float32), axis=0)
    images_with_detections = draw_bounding_boxes_on_image_tensors(
        tf.expand_dims(
            eval_dict[input_data_fields.original_image][indx], axis=0),
        tf.expand_dims(
            eval_dict[detection_fields.detection_boxes][indx], axis=0),
        tf.expand_dims(
            eval_dict[detection_fields.detection_classes][indx], axis=0),
        tf.expand_dims(
            eval_dict[detection_fields.detection_scores][indx], axis=0),
        category_index,
        original_image_spatial_shape=tf.expand_dims(
            eval_dict[input_data_fields.original_image_spatial_shape][indx],
            axis=0),
        true_image_shape=tf.expand_dims(
            eval_dict[input_data_fields.true_image_shape][indx], axis=0),
        instance_masks=instance_masks,
        keypoints=keypoints,
        keypoint_scores=keypoint_scores,
        keypoint_edges=keypoint_edges,
        max_boxes_to_draw=max_boxes_to_draw,
        min_score_thresh=min_score_thresh,
        use_normalized_coordinates=use_normalized_coordinates)
    num_gt_boxes_i = num_gt_boxes[indx]
    images_with_groundtruth = draw_bounding_boxes_on_image_tensors(
        tf.expand_dims(
            eval_dict[input_data_fields.original_image][indx],
            axis=0),
        tf.expand_dims(
            eval_dict[input_data_fields.groundtruth_boxes][indx]
            [:num_gt_boxes_i],
            axis=0),
        tf.expand_dims(
            eval_dict[input_data_fields.groundtruth_classes][indx]
            [:num_gt_boxes_i],
            axis=0),
        tf.expand_dims(
            tf.ones_like(
                eval_dict[input_data_fields.groundtruth_classes][indx]
                [:num_gt_boxes_i],
                dtype=tf.float32),
            axis=0),
        category_index,
        original_image_spatial_shape=tf.expand_dims(
            eval_dict[input_data_fields.original_image_spatial_shape][indx],
            axis=0),
        true_image_shape=tf.expand_dims(
            eval_dict[input_data_fields.true_image_shape][indx], axis=0),
        instance_masks=groundtruth_instance_masks,
        keypoints=groundtruth_keypoints,
        keypoint_scores=groundtruth_keypoint_scores,
        keypoint_edges=keypoint_edges,
        max_boxes_to_draw=None,
        min_score_thresh=0.0,
        use_normalized_coordinates=use_normalized_coordinates)
    images_to_visualize = tf.concat([images_with_detections,
                                     images_with_groundtruth], axis=2)

    if input_data_fields.image_additional_channels in eval_dict:
      images_with_additional_channels_groundtruth = (
          draw_bounding_boxes_on_image_tensors(
              tf.expand_dims(
                  eval_dict[input_data_fields.image_additional_channels][indx],
                  axis=0),
              tf.expand_dims(
                  eval_dict[input_data_fields.groundtruth_boxes][indx]
                  [:num_gt_boxes_i],
                  axis=0),
              tf.expand_dims(
                  eval_dict[input_data_fields.groundtruth_classes][indx]
                  [:num_gt_boxes_i],
                  axis=0),
              tf.expand_dims(
                  tf.ones_like(
                      eval_dict[input_data_fields.groundtruth_classes][indx]
                      [num_gt_boxes_i],
                      dtype=tf.float32),
                  axis=0),
              category_index,
              original_image_spatial_shape=tf.expand_dims(
                  eval_dict[input_data_fields.original_image_spatial_shape]
                  [indx],
                  axis=0),
              true_image_shape=tf.expand_dims(
                  eval_dict[input_data_fields.true_image_shape][indx], axis=0),
              instance_masks=groundtruth_instance_masks,
              keypoints=None,
              keypoint_edges=None,
              max_boxes_to_draw=None,
              min_score_thresh=0.0,
              use_normalized_coordinates=use_normalized_coordinates))
      images_to_visualize = tf.concat(
          [images_to_visualize, images_with_additional_channels_groundtruth],
          axis=2)
    images_with_detections_list.append(images_to_visualize)

  return images_with_detections_list