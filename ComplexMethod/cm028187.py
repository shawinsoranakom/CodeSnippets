def _prepare_groundtruth_for_eval(detection_model, class_agnostic,
                                  max_number_of_boxes):
  """Extracts groundtruth data from detection_model and prepares it for eval.

  Args:
    detection_model: A `DetectionModel` object.
    class_agnostic: Whether the detections are class_agnostic.
    max_number_of_boxes: Max number of groundtruth boxes.

  Returns:
    A tuple of:
    groundtruth: Dictionary with the following fields:
      'groundtruth_boxes': [batch_size, num_boxes, 4] float32 tensor of boxes,
        in normalized coordinates.
      'groundtruth_classes': [batch_size, num_boxes] int64 tensor of 1-indexed
        classes.
      'groundtruth_masks': 4D float32 tensor of instance masks (if provided in
        groundtruth)
      'groundtruth_is_crowd': [batch_size, num_boxes] bool tensor indicating
        is_crowd annotations (if provided in groundtruth).
      'groundtruth_area': [batch_size, num_boxes] float32 tensor indicating
        the area (in the original absolute coordinates) of annotations (if
        provided in groundtruth).
      'num_groundtruth_boxes': [batch_size] tensor containing the maximum number
        of groundtruth boxes per image..
      'groundtruth_keypoints': [batch_size, num_boxes, num_keypoints, 2] float32
        tensor of keypoints (if provided in groundtruth).
      'groundtruth_dp_num_points_list': [batch_size, num_boxes] int32 tensor
        with the number of DensePose points for each instance (if provided in
        groundtruth).
      'groundtruth_dp_part_ids_list': [batch_size, num_boxes,
        max_sampled_points] int32 tensor with the part ids for each DensePose
        sampled point (if provided in groundtruth).
      'groundtruth_dp_surface_coords_list': [batch_size, num_boxes,
        max_sampled_points, 4] containing the DensePose surface coordinates for
        each sampled point (if provided in groundtruth).
      'groundtruth_track_ids_list': [batch_size, num_boxes] int32 tensor
        with track ID for each instance (if provided in groundtruth).
      'groundtruth_group_of': [batch_size, num_boxes] bool tensor indicating
        group_of annotations (if provided in groundtruth).
      'groundtruth_labeled_classes': [batch_size, num_classes] int64
        tensor of 1-indexed classes.
      'groundtruth_verified_neg_classes': [batch_size, num_classes] float32
        K-hot representation of 1-indexed classes which were verified as not
        present in the image.
      'groundtruth_not_exhaustive_classes': [batch_size, num_classes] K-hot
        representation of 1-indexed classes which don't have all of their
        instances marked exhaustively.
      'input_data_fields.groundtruth_image_classes': integer representation of
        the classes that were sent for verification for a given image. Note that
        this field does not support batching as the number of classes can be
        variable.
    class_agnostic: Boolean indicating whether detections are class agnostic.
  """
  input_data_fields = fields.InputDataFields()
  groundtruth_boxes = tf.stack(
      detection_model.groundtruth_lists(fields.BoxListFields.boxes))
  groundtruth_boxes_shape = tf.shape(groundtruth_boxes)
  # For class-agnostic models, groundtruth one-hot encodings collapse to all
  # ones.
  if class_agnostic:
    groundtruth_classes_one_hot = tf.ones(
        [groundtruth_boxes_shape[0], groundtruth_boxes_shape[1], 1])
  else:
    groundtruth_classes_one_hot = tf.stack(
        detection_model.groundtruth_lists(fields.BoxListFields.classes))
  label_id_offset = 1  # Applying label id offset (b/63711816)
  groundtruth_classes = (
      tf.argmax(groundtruth_classes_one_hot, axis=2) + label_id_offset)
  groundtruth = {
      input_data_fields.groundtruth_boxes: groundtruth_boxes,
      input_data_fields.groundtruth_classes: groundtruth_classes
  }

  if detection_model.groundtruth_has_field(
      input_data_fields.groundtruth_image_classes):
    groundtruth_image_classes_k_hot = tf.stack(
        detection_model.groundtruth_lists(
            input_data_fields.groundtruth_image_classes))
    groundtruth_image_classes = tf.expand_dims(
        tf.where(groundtruth_image_classes_k_hot > 0)[:, 1], 0)
    # Adds back label_id_offset as it is subtracted in
    # convert_labeled_classes_to_k_hot.
    groundtruth[
        input_data_fields.
        groundtruth_image_classes] = groundtruth_image_classes + label_id_offset

  if detection_model.groundtruth_has_field(fields.BoxListFields.masks):
    groundtruth[input_data_fields.groundtruth_instance_masks] = tf.stack(
        detection_model.groundtruth_lists(fields.BoxListFields.masks))

  if detection_model.groundtruth_has_field(fields.BoxListFields.is_crowd):
    groundtruth[input_data_fields.groundtruth_is_crowd] = tf.stack(
        detection_model.groundtruth_lists(fields.BoxListFields.is_crowd))

  if detection_model.groundtruth_has_field(input_data_fields.groundtruth_area):
    groundtruth[input_data_fields.groundtruth_area] = tf.stack(
        detection_model.groundtruth_lists(input_data_fields.groundtruth_area))

  if detection_model.groundtruth_has_field(fields.BoxListFields.keypoints):
    groundtruth[input_data_fields.groundtruth_keypoints] = tf.stack(
        detection_model.groundtruth_lists(fields.BoxListFields.keypoints))

  if detection_model.groundtruth_has_field(
      fields.BoxListFields.keypoint_depths):
    groundtruth[input_data_fields.groundtruth_keypoint_depths] = tf.stack(
        detection_model.groundtruth_lists(fields.BoxListFields.keypoint_depths))
    groundtruth[
        input_data_fields.groundtruth_keypoint_depth_weights] = tf.stack(
            detection_model.groundtruth_lists(
                fields.BoxListFields.keypoint_depth_weights))

  if detection_model.groundtruth_has_field(
      fields.BoxListFields.keypoint_visibilities):
    groundtruth[input_data_fields.groundtruth_keypoint_visibilities] = tf.stack(
        detection_model.groundtruth_lists(
            fields.BoxListFields.keypoint_visibilities))

  if detection_model.groundtruth_has_field(fields.BoxListFields.group_of):
    groundtruth[input_data_fields.groundtruth_group_of] = tf.stack(
        detection_model.groundtruth_lists(fields.BoxListFields.group_of))

  label_id_offset_paddings = tf.constant([[0, 0], [1, 0]])
  if detection_model.groundtruth_has_field(
      input_data_fields.groundtruth_verified_neg_classes):
    groundtruth[input_data_fields.groundtruth_verified_neg_classes] = tf.pad(
        tf.stack(
            detection_model.groundtruth_lists(
                input_data_fields.groundtruth_verified_neg_classes)),
        label_id_offset_paddings)

  if detection_model.groundtruth_has_field(
      input_data_fields.groundtruth_not_exhaustive_classes):
    groundtruth[input_data_fields.groundtruth_not_exhaustive_classes] = tf.pad(
        tf.stack(
            detection_model.groundtruth_lists(
                input_data_fields.groundtruth_not_exhaustive_classes)),
        label_id_offset_paddings)

  if detection_model.groundtruth_has_field(
      fields.BoxListFields.densepose_num_points):
    groundtruth[input_data_fields.groundtruth_dp_num_points] = tf.stack(
        detection_model.groundtruth_lists(
            fields.BoxListFields.densepose_num_points))
  if detection_model.groundtruth_has_field(
      fields.BoxListFields.densepose_part_ids):
    groundtruth[input_data_fields.groundtruth_dp_part_ids] = tf.stack(
        detection_model.groundtruth_lists(
            fields.BoxListFields.densepose_part_ids))
  if detection_model.groundtruth_has_field(
      fields.BoxListFields.densepose_surface_coords):
    groundtruth[input_data_fields.groundtruth_dp_surface_coords] = tf.stack(
        detection_model.groundtruth_lists(
            fields.BoxListFields.densepose_surface_coords))

  if detection_model.groundtruth_has_field(fields.BoxListFields.track_ids):
    groundtruth[input_data_fields.groundtruth_track_ids] = tf.stack(
        detection_model.groundtruth_lists(fields.BoxListFields.track_ids))

  if detection_model.groundtruth_has_field(
      input_data_fields.groundtruth_labeled_classes):
    groundtruth[input_data_fields.groundtruth_labeled_classes] = tf.pad(
        tf.stack(
            detection_model.groundtruth_lists(
                input_data_fields.groundtruth_labeled_classes)),
        label_id_offset_paddings)

  groundtruth[input_data_fields.num_groundtruth_boxes] = (
      tf.tile([max_number_of_boxes], multiples=[groundtruth_boxes_shape[0]]))
  return groundtruth