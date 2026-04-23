def result_dict_for_batched_example(images,
                                    keys,
                                    detections,
                                    groundtruth=None,
                                    class_agnostic=False,
                                    scale_to_absolute=False,
                                    original_image_spatial_shapes=None,
                                    true_image_shapes=None,
                                    max_gt_boxes=None,
                                    label_id_offset=1):
  """Merges all detection and groundtruth information for a single example.

  Note that evaluation tools require classes that are 1-indexed, and so this
  function performs the offset. If `class_agnostic` is True, all output classes
  have label 1.
  The groundtruth coordinates of boxes/keypoints in 'groundtruth' dictionary are
  normalized relative to the (potentially padded) input image, while the
  coordinates in 'detection' dictionary are normalized relative to the true
  image shape.

  Args:
    images: A single 4D uint8 image tensor of shape [batch_size, H, W, C].
    keys: A [batch_size] string/int tensor with image identifier.
    detections: A dictionary of detections, returned from
      DetectionModel.postprocess().
    groundtruth: (Optional) Dictionary of groundtruth items, with fields:
      'groundtruth_boxes': [batch_size, max_number_of_boxes, 4] float32 tensor
        of boxes, in normalized coordinates.
      'groundtruth_classes':  [batch_size, max_number_of_boxes] int64 tensor of
        1-indexed classes.
      'groundtruth_area': [batch_size, max_number_of_boxes] float32 tensor of
        bbox area. (Optional)
      'groundtruth_is_crowd':[batch_size, max_number_of_boxes] int64
        tensor. (Optional)
      'groundtruth_difficult': [batch_size, max_number_of_boxes] int64
        tensor. (Optional)
      'groundtruth_group_of': [batch_size, max_number_of_boxes] int64
        tensor. (Optional)
      'groundtruth_instance_masks': 4D int64 tensor of instance
        masks (Optional).
      'groundtruth_keypoints': [batch_size, max_number_of_boxes, num_keypoints,
        2] float32 tensor with keypoints (Optional).
      'groundtruth_keypoint_visibilities': [batch_size, max_number_of_boxes,
        num_keypoints] bool tensor with keypoint visibilities (Optional).
      'groundtruth_labeled_classes': [batch_size, num_classes] int64
        tensor of 1-indexed classes. (Optional)
      'groundtruth_dp_num_points': [batch_size, max_number_of_boxes] int32
        tensor. (Optional)
      'groundtruth_dp_part_ids': [batch_size, max_number_of_boxes,
        max_sampled_points] int32 tensor. (Optional)
      'groundtruth_dp_surface_coords_list': [batch_size, max_number_of_boxes,
        max_sampled_points, 4] float32 tensor. (Optional)
    class_agnostic: Boolean indicating whether the detections are class-agnostic
      (i.e. binary). Default False.
    scale_to_absolute: Boolean indicating whether boxes and keypoints should be
      scaled to absolute coordinates. Note that for IoU based evaluations, it
      does not matter whether boxes are expressed in absolute or relative
      coordinates. Default False.
    original_image_spatial_shapes: A 2D int32 tensor of shape [batch_size, 2]
      used to resize the image. When set to None, the image size is retained.
    true_image_shapes: A 2D int32 tensor of shape [batch_size, 3]
      containing the size of the unpadded original_image.
    max_gt_boxes: [batch_size] tensor representing the maximum number of
      groundtruth boxes to pad.
    label_id_offset: offset for class ids.

  Returns:
    A dictionary with:
    'original_image': A [batch_size, H, W, C] uint8 image tensor.
    'original_image_spatial_shape': A [batch_size, 2] tensor containing the
      original image sizes.
    'true_image_shape': A [batch_size, 3] tensor containing the size of
      the unpadded original_image.
    'key': A [batch_size] string tensor with image identifier.
    'detection_boxes': [batch_size, max_detections, 4] float32 tensor of boxes,
      in normalized or absolute coordinates, depending on the value of
      `scale_to_absolute`.
    'detection_scores': [batch_size, max_detections] float32 tensor of scores.
    'detection_classes': [batch_size, max_detections] int64 tensor of 1-indexed
      classes.
    'detection_masks': [batch_size, max_detections, H, W] uint8 tensor of
      instance masks, reframed to full image masks. Note that these may be
      binarized (e.g. {0, 1}), or may contain 1-indexed part labels. (Optional)
    'detection_keypoints': [batch_size, max_detections, num_keypoints, 2]
      float32 tensor containing keypoint coordinates. (Optional)
    'detection_keypoint_scores': [batch_size, max_detections, num_keypoints]
      float32 tensor containing keypoint scores. (Optional)
    'detection_surface_coords': [batch_size, max_detection, H, W, 2] float32
      tensor with normalized surface coordinates (e.g. DensePose UV
      coordinates). (Optional)
    'num_detections': [batch_size] int64 tensor containing number of valid
      detections.
    'groundtruth_boxes': [batch_size, num_boxes, 4] float32 tensor of boxes, in
      normalized or absolute coordinates, depending on the value of
      `scale_to_absolute`. (Optional)
    'groundtruth_classes': [batch_size, num_boxes] int64 tensor of 1-indexed
      classes. (Optional)
    'groundtruth_area': [batch_size, num_boxes] float32 tensor of bbox
      area. (Optional)
    'groundtruth_is_crowd': [batch_size, num_boxes] int64 tensor. (Optional)
    'groundtruth_difficult': [batch_size, num_boxes] int64 tensor. (Optional)
    'groundtruth_group_of': [batch_size, num_boxes] int64 tensor. (Optional)
    'groundtruth_instance_masks': 4D int64 tensor of instance masks
      (Optional).
    'groundtruth_keypoints': [batch_size, num_boxes, num_keypoints, 2] float32
      tensor with keypoints (Optional).
    'groundtruth_keypoint_visibilities': [batch_size, num_boxes, num_keypoints]
      bool tensor with keypoint visibilities (Optional).
    'groundtruth_labeled_classes': [batch_size, num_classes]  int64 tensor
      of 1-indexed classes. (Optional)
    'num_groundtruth_boxes': [batch_size] tensor containing the maximum number
      of groundtruth boxes per image.

  Raises:
    ValueError: if original_image_spatial_shape is not 2D int32 tensor of shape
      [2].
    ValueError: if true_image_shapes is not 2D int32 tensor of shape
      [3].
  """
  input_data_fields = fields.InputDataFields
  if original_image_spatial_shapes is None:
    original_image_spatial_shapes = tf.tile(
        tf.expand_dims(tf.shape(images)[1:3], axis=0),
        multiples=[tf.shape(images)[0], 1])
  else:
    if (len(original_image_spatial_shapes.shape) != 2 and
        original_image_spatial_shapes.shape[1] != 2):
      raise ValueError(
          '`original_image_spatial_shape` should be a 2D tensor of shape '
          '[batch_size, 2].')

  if true_image_shapes is None:
    true_image_shapes = tf.tile(
        tf.expand_dims(tf.shape(images)[1:4], axis=0),
        multiples=[tf.shape(images)[0], 1])
  else:
    if (len(true_image_shapes.shape) != 2
        and true_image_shapes.shape[1] != 3):
      raise ValueError('`true_image_shapes` should be a 2D tensor of '
                       'shape [batch_size, 3].')

  output_dict = {
      input_data_fields.original_image:
          images,
      input_data_fields.key:
          keys,
      input_data_fields.original_image_spatial_shape: (
          original_image_spatial_shapes),
      input_data_fields.true_image_shape:
          true_image_shapes
  }

  detection_fields = fields.DetectionResultFields
  detection_boxes = detections[detection_fields.detection_boxes]
  detection_scores = detections[detection_fields.detection_scores]
  num_detections = tf.cast(detections[detection_fields.num_detections],
                           dtype=tf.int32)

  if class_agnostic:
    detection_classes = tf.ones_like(detection_scores, dtype=tf.int64)
  else:
    detection_classes = (
        tf.to_int64(detections[detection_fields.detection_classes]) +
        label_id_offset)

  if scale_to_absolute:
    output_dict[detection_fields.detection_boxes] = (
        shape_utils.static_or_dynamic_map_fn(
            _scale_box_to_absolute,
            elems=[detection_boxes, original_image_spatial_shapes],
            dtype=tf.float32))
  else:
    output_dict[detection_fields.detection_boxes] = detection_boxes
  output_dict[detection_fields.detection_classes] = detection_classes
  output_dict[detection_fields.detection_scores] = detection_scores
  output_dict[detection_fields.num_detections] = num_detections

  if detection_fields.detection_masks in detections:
    detection_masks = detections[detection_fields.detection_masks]
    output_dict[detection_fields.detection_masks] = resize_detection_masks(
        detection_boxes, detection_masks, original_image_spatial_shapes)

    if detection_fields.detection_surface_coords in detections:
      detection_surface_coords = detections[
          detection_fields.detection_surface_coords]
      output_dict[detection_fields.detection_surface_coords] = (
          shape_utils.static_or_dynamic_map_fn(
              _resize_surface_coordinate_masks,
              elems=[detection_boxes, detection_surface_coords,
                     original_image_spatial_shapes],
              dtype=tf.float32))

  if detection_fields.detection_keypoints in detections:
    detection_keypoints = detections[detection_fields.detection_keypoints]
    output_dict[detection_fields.detection_keypoints] = detection_keypoints
    if scale_to_absolute:
      output_dict[detection_fields.detection_keypoints] = (
          shape_utils.static_or_dynamic_map_fn(
              _scale_keypoint_to_absolute,
              elems=[detection_keypoints, original_image_spatial_shapes],
              dtype=tf.float32))
    if detection_fields.detection_keypoint_scores in detections:
      output_dict[detection_fields.detection_keypoint_scores] = detections[
          detection_fields.detection_keypoint_scores]
    else:
      output_dict[detection_fields.detection_keypoint_scores] = tf.ones_like(
          detections[detection_fields.detection_keypoints][:, :, :, 0])

  if groundtruth:
    if max_gt_boxes is None:
      if input_data_fields.num_groundtruth_boxes in groundtruth:
        max_gt_boxes = groundtruth[input_data_fields.num_groundtruth_boxes]
      else:
        raise ValueError(
            'max_gt_boxes must be provided when processing batched examples.')

    if input_data_fields.groundtruth_instance_masks in groundtruth:
      masks = groundtruth[input_data_fields.groundtruth_instance_masks]
      max_spatial_shape = tf.reduce_max(
          original_image_spatial_shapes, axis=0, keep_dims=True)
      tiled_max_spatial_shape = tf.tile(
          max_spatial_shape,
          multiples=[tf.shape(original_image_spatial_shapes)[0], 1])
      groundtruth[input_data_fields.groundtruth_instance_masks] = (
          shape_utils.static_or_dynamic_map_fn(
              _resize_groundtruth_masks,
              elems=[masks, true_image_shapes,
                     original_image_spatial_shapes,
                     tiled_max_spatial_shape],
              dtype=tf.uint8))

    output_dict.update(groundtruth)

    image_shape = tf.cast(tf.shape(images), tf.float32)
    image_height, image_width = image_shape[1], image_shape[2]

    def _scale_box_to_normalized_true_image(args):
      """Scale the box coordinates to be relative to the true image shape."""
      boxes, true_image_shape = args
      true_image_shape = tf.cast(true_image_shape, tf.float32)
      true_height, true_width = true_image_shape[0], true_image_shape[1]
      normalized_window = tf.stack([0.0, 0.0, true_height / image_height,
                                    true_width / image_width])
      return box_list_ops.change_coordinate_frame(
          box_list.BoxList(boxes), normalized_window).get()

    groundtruth_boxes = groundtruth[input_data_fields.groundtruth_boxes]
    groundtruth_boxes = shape_utils.static_or_dynamic_map_fn(
        _scale_box_to_normalized_true_image,
        elems=[groundtruth_boxes, true_image_shapes], dtype=tf.float32)
    output_dict[input_data_fields.groundtruth_boxes] = groundtruth_boxes

    if input_data_fields.groundtruth_keypoints in groundtruth:
      # If groundtruth_keypoints is in the groundtruth dictionary. Update the
      # coordinates to conform with the true image shape.
      def _scale_keypoints_to_normalized_true_image(args):
        """Scale the box coordinates to be relative to the true image shape."""
        keypoints, true_image_shape = args
        true_image_shape = tf.cast(true_image_shape, tf.float32)
        true_height, true_width = true_image_shape[0], true_image_shape[1]
        normalized_window = tf.stack(
            [0.0, 0.0, true_height / image_height, true_width / image_width])
        return keypoint_ops.change_coordinate_frame(keypoints,
                                                    normalized_window)

      groundtruth_keypoints = groundtruth[
          input_data_fields.groundtruth_keypoints]
      groundtruth_keypoints = shape_utils.static_or_dynamic_map_fn(
          _scale_keypoints_to_normalized_true_image,
          elems=[groundtruth_keypoints, true_image_shapes],
          dtype=tf.float32)
      output_dict[
          input_data_fields.groundtruth_keypoints] = groundtruth_keypoints

    if scale_to_absolute:
      groundtruth_boxes = output_dict[input_data_fields.groundtruth_boxes]
      output_dict[input_data_fields.groundtruth_boxes] = (
          shape_utils.static_or_dynamic_map_fn(
              _scale_box_to_absolute,
              elems=[groundtruth_boxes, original_image_spatial_shapes],
              dtype=tf.float32))
      if input_data_fields.groundtruth_keypoints in groundtruth:
        groundtruth_keypoints = output_dict[
            input_data_fields.groundtruth_keypoints]
        output_dict[input_data_fields.groundtruth_keypoints] = (
            shape_utils.static_or_dynamic_map_fn(
                _scale_keypoint_to_absolute,
                elems=[groundtruth_keypoints, original_image_spatial_shapes],
                dtype=tf.float32))

    # For class-agnostic models, groundtruth classes all become 1.
    if class_agnostic:
      groundtruth_classes = groundtruth[input_data_fields.groundtruth_classes]
      groundtruth_classes = tf.ones_like(groundtruth_classes, dtype=tf.int64)
      output_dict[input_data_fields.groundtruth_classes] = groundtruth_classes

    output_dict[input_data_fields.num_groundtruth_boxes] = max_gt_boxes

  return output_dict