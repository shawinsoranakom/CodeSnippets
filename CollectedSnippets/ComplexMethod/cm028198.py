def transform_input_data(tensor_dict,
                         model_preprocess_fn,
                         image_resizer_fn,
                         num_classes,
                         data_augmentation_fn=None,
                         merge_multiple_boxes=False,
                         retain_original_image=False,
                         use_multiclass_scores=False,
                         use_bfloat16=False,
                         retain_original_image_additional_channels=False,
                         keypoint_type_weight=None,
                         image_classes_field_map_empty_to_ones=True):
  """A single function that is responsible for all input data transformations.

  Data transformation functions are applied in the following order.
  1. If key fields.InputDataFields.image_additional_channels is present in
     tensor_dict, the additional channels will be merged into
     fields.InputDataFields.image.
  2. data_augmentation_fn (optional): applied on tensor_dict.
  3. model_preprocess_fn: applied only on image tensor in tensor_dict.
  4. keypoint_type_weight (optional): If groundtruth keypoints are in
     the tensor dictionary, per-keypoint weights are produced. These weights are
     initialized by `keypoint_type_weight` (or ones if left None).
     Then, for all keypoints that are not visible, the weights are set to 0 (to
     avoid penalizing the model in a loss function).
  5. image_resizer_fn: applied on original image and instance mask tensor in
     tensor_dict.
  6. one_hot_encoding: applied to classes tensor in tensor_dict.
  7. merge_multiple_boxes (optional): when groundtruth boxes are exactly the
     same they can be merged into a single box with an associated k-hot class
     label.

  Args:
    tensor_dict: dictionary containing input tensors keyed by
      fields.InputDataFields.
    model_preprocess_fn: model's preprocess function to apply on image tensor.
      This function must take in a 4-D float tensor and return a 4-D preprocess
      float tensor and a tensor containing the true image shape.
    image_resizer_fn: image resizer function to apply on groundtruth instance
      `masks. This function must take a 3-D float tensor of an image and a 3-D
      tensor of instance masks and return a resized version of these along with
      the true shapes.
    num_classes: number of max classes to one-hot (or k-hot) encode the class
      labels.
    data_augmentation_fn: (optional) data augmentation function to apply on
      input `tensor_dict`.
    merge_multiple_boxes: (optional) whether to merge multiple groundtruth boxes
      and classes for a given image if the boxes are exactly the same.
    retain_original_image: (optional) whether to retain original image in the
      output dictionary.
    use_multiclass_scores: whether to use multiclass scores as class targets
      instead of one-hot encoding of `groundtruth_classes`. When
      this is True and multiclass_scores is empty, one-hot encoding of
      `groundtruth_classes` is used as a fallback.
    use_bfloat16: (optional) a bool, whether to use bfloat16 in training.
    retain_original_image_additional_channels: (optional) Whether to retain
      original image additional channels in the output dictionary.
    keypoint_type_weight: A list (of length num_keypoints) containing
      groundtruth loss weights to use for each keypoint. If None, will use a
      weight of 1.
    image_classes_field_map_empty_to_ones: A boolean flag indicating if empty
      image classes field indicates that all classes have been labeled on this
      image [true] or none [false].

  Returns:
    A dictionary keyed by fields.InputDataFields containing the tensors obtained
    after applying all the transformations.

  Raises:
    KeyError: If both groundtruth_labeled_classes and groundtruth_image_classes
      are provided by the decoder in tensor_dict since both fields are
      considered to contain the same information.
  """
  out_tensor_dict = tensor_dict.copy()

  input_fields = fields.InputDataFields
  labeled_classes_field = input_fields.groundtruth_labeled_classes
  image_classes_field = input_fields.groundtruth_image_classes
  verified_neg_classes_field = input_fields.groundtruth_verified_neg_classes
  not_exhaustive_field = input_fields.groundtruth_not_exhaustive_classes

  if (labeled_classes_field in out_tensor_dict and
      image_classes_field in out_tensor_dict):
    raise KeyError('groundtruth_labeled_classes and groundtruth_image_classes'
                   'are provided by the decoder, but only one should be set.')

  for field, map_empty_to_ones in [(labeled_classes_field, True),
                                   (image_classes_field,
                                    image_classes_field_map_empty_to_ones),
                                   (verified_neg_classes_field, False),
                                   (not_exhaustive_field, False)]:
    if field in out_tensor_dict:
      out_tensor_dict[field] = _remove_unrecognized_classes(
          out_tensor_dict[field], unrecognized_label=-1)
      out_tensor_dict[field] = convert_labeled_classes_to_k_hot(
          out_tensor_dict[field], num_classes, map_empty_to_ones)

  if input_fields.multiclass_scores in out_tensor_dict:
    out_tensor_dict[
        input_fields
        .multiclass_scores] = _multiclass_scores_or_one_hot_labels(
            out_tensor_dict[input_fields.multiclass_scores],
            out_tensor_dict[input_fields.groundtruth_boxes],
            out_tensor_dict[input_fields.groundtruth_classes],
            num_classes)

  if input_fields.groundtruth_boxes in out_tensor_dict:
    out_tensor_dict = util_ops.filter_groundtruth_with_nan_box_coordinates(
        out_tensor_dict)
    out_tensor_dict = util_ops.filter_unrecognized_classes(out_tensor_dict)

  if retain_original_image:
    out_tensor_dict[input_fields.original_image] = tf.cast(
        image_resizer_fn(out_tensor_dict[input_fields.image],
                         None)[0], tf.uint8)

  if input_fields.image_additional_channels in out_tensor_dict:
    channels = out_tensor_dict[input_fields.image_additional_channels]
    out_tensor_dict[input_fields.image] = tf.concat(
        [out_tensor_dict[input_fields.image], channels], axis=2)
    if retain_original_image_additional_channels:
      out_tensor_dict[
          input_fields.image_additional_channels] = tf.cast(
              image_resizer_fn(channels, None)[0], tf.uint8)

  # Apply data augmentation ops.
  if data_augmentation_fn is not None:
    out_tensor_dict = data_augmentation_fn(out_tensor_dict)

  # Apply model preprocessing ops and resize instance masks.
  image = out_tensor_dict[input_fields.image]
  preprocessed_resized_image, true_image_shape = model_preprocess_fn(
      tf.expand_dims(tf.cast(image, dtype=tf.float32), axis=0))

  preprocessed_shape = tf.shape(preprocessed_resized_image)
  new_height, new_width = preprocessed_shape[1], preprocessed_shape[2]

  im_box = tf.stack([
      0.0, 0.0,
      tf.to_float(new_height) / tf.to_float(true_image_shape[0, 0]),
      tf.to_float(new_width) / tf.to_float(true_image_shape[0, 1])
  ])

  if input_fields.groundtruth_boxes in tensor_dict:
    bboxes = out_tensor_dict[input_fields.groundtruth_boxes]
    boxlist = box_list.BoxList(bboxes)
    realigned_bboxes = box_list_ops.change_coordinate_frame(boxlist, im_box)

    realigned_boxes_tensor = realigned_bboxes.get()
    valid_boxes_tensor = assert_or_prune_invalid_boxes(realigned_boxes_tensor)
    out_tensor_dict[
        input_fields.groundtruth_boxes] = valid_boxes_tensor

  if input_fields.groundtruth_keypoints in tensor_dict:
    keypoints = out_tensor_dict[input_fields.groundtruth_keypoints]
    realigned_keypoints = keypoint_ops.change_coordinate_frame(keypoints,
                                                               im_box)
    out_tensor_dict[
        input_fields.groundtruth_keypoints] = realigned_keypoints
    flds_gt_kpt = input_fields.groundtruth_keypoints
    flds_gt_kpt_vis = input_fields.groundtruth_keypoint_visibilities
    flds_gt_kpt_weights = input_fields.groundtruth_keypoint_weights
    if flds_gt_kpt_vis not in out_tensor_dict:
      out_tensor_dict[flds_gt_kpt_vis] = tf.ones_like(
          out_tensor_dict[flds_gt_kpt][:, :, 0],
          dtype=tf.bool)
    flds_gt_kpt_depth = fields.InputDataFields.groundtruth_keypoint_depths
    flds_gt_kpt_depth_weight = (
        fields.InputDataFields.groundtruth_keypoint_depth_weights)
    if flds_gt_kpt_depth in out_tensor_dict:
      out_tensor_dict[flds_gt_kpt_depth] = out_tensor_dict[flds_gt_kpt_depth]
      out_tensor_dict[flds_gt_kpt_depth_weight] = out_tensor_dict[
          flds_gt_kpt_depth_weight]

    out_tensor_dict[flds_gt_kpt_weights] = (
        keypoint_ops.keypoint_weights_from_visibilities(
            out_tensor_dict[flds_gt_kpt_vis],
            keypoint_type_weight))

  dp_surface_coords_fld = input_fields.groundtruth_dp_surface_coords
  if dp_surface_coords_fld in tensor_dict:
    dp_surface_coords = out_tensor_dict[dp_surface_coords_fld]
    realigned_dp_surface_coords = densepose_ops.change_coordinate_frame(
        dp_surface_coords, im_box)
    out_tensor_dict[dp_surface_coords_fld] = realigned_dp_surface_coords

  if use_bfloat16:
    preprocessed_resized_image = tf.cast(
        preprocessed_resized_image, tf.bfloat16)
    if input_fields.context_features in out_tensor_dict:
      out_tensor_dict[input_fields.context_features] = tf.cast(
          out_tensor_dict[input_fields.context_features], tf.bfloat16)
  out_tensor_dict[input_fields.image] = tf.squeeze(
      preprocessed_resized_image, axis=0)
  out_tensor_dict[input_fields.true_image_shape] = tf.squeeze(
      true_image_shape, axis=0)
  if input_fields.groundtruth_instance_masks in out_tensor_dict:
    masks = out_tensor_dict[input_fields.groundtruth_instance_masks]
    _, resized_masks, _ = image_resizer_fn(image, masks)
    if use_bfloat16:
      resized_masks = tf.cast(resized_masks, tf.bfloat16)
    out_tensor_dict[
        input_fields.groundtruth_instance_masks] = resized_masks

  zero_indexed_groundtruth_classes = out_tensor_dict[
      input_fields.groundtruth_classes] - _LABEL_OFFSET
  if use_multiclass_scores:
    out_tensor_dict[
        input_fields.groundtruth_classes] = out_tensor_dict[
            input_fields.multiclass_scores]
  else:
    out_tensor_dict[input_fields.groundtruth_classes] = tf.one_hot(
        zero_indexed_groundtruth_classes, num_classes)
  out_tensor_dict.pop(input_fields.multiclass_scores, None)

  if input_fields.groundtruth_confidences in out_tensor_dict:
    groundtruth_confidences = out_tensor_dict[
        input_fields.groundtruth_confidences]
    # Map the confidences to the one-hot encoding of classes
    out_tensor_dict[input_fields.groundtruth_confidences] = (
        tf.reshape(groundtruth_confidences, [-1, 1]) *
        out_tensor_dict[input_fields.groundtruth_classes])
  else:
    groundtruth_confidences = tf.ones_like(
        zero_indexed_groundtruth_classes, dtype=tf.float32)
    out_tensor_dict[input_fields.groundtruth_confidences] = (
        out_tensor_dict[input_fields.groundtruth_classes])

  if merge_multiple_boxes:
    merged_boxes, merged_classes, merged_confidences, _ = (
        util_ops.merge_boxes_with_multiple_labels(
            out_tensor_dict[input_fields.groundtruth_boxes],
            zero_indexed_groundtruth_classes,
            groundtruth_confidences,
            num_classes))
    merged_classes = tf.cast(merged_classes, tf.float32)
    out_tensor_dict[input_fields.groundtruth_boxes] = merged_boxes
    out_tensor_dict[input_fields.groundtruth_classes] = merged_classes
    out_tensor_dict[input_fields.groundtruth_confidences] = (
        merged_confidences)
  if input_fields.groundtruth_boxes in out_tensor_dict:
    out_tensor_dict[input_fields.num_groundtruth_boxes] = tf.shape(
        out_tensor_dict[input_fields.groundtruth_boxes])[0]

  return out_tensor_dict