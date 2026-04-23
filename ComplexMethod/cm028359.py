def retain_groundtruth(tensor_dict, valid_indices):
  """Retains groundtruth by valid indices.

  Args:
    tensor_dict: a dictionary of following groundtruth tensors -
      fields.InputDataFields.groundtruth_boxes
      fields.InputDataFields.groundtruth_classes
      fields.InputDataFields.groundtruth_confidences
      fields.InputDataFields.groundtruth_keypoints
      fields.InputDataFields.groundtruth_instance_masks
      fields.InputDataFields.groundtruth_is_crowd
      fields.InputDataFields.groundtruth_area
      fields.InputDataFields.groundtruth_label_types
      fields.InputDataFields.groundtruth_difficult
    valid_indices: a tensor with valid indices for the box-level groundtruth.

  Returns:
    a dictionary of tensors containing only the groundtruth for valid_indices.

  Raises:
    ValueError: If the shape of valid_indices is invalid.
    ValueError: field fields.InputDataFields.groundtruth_boxes is
      not present in tensor_dict.
  """
  input_shape = valid_indices.get_shape().as_list()
  if not (len(input_shape) == 1 or
          (len(input_shape) == 2 and input_shape[1] == 1)):
    raise ValueError('The shape of valid_indices is invalid.')
  valid_indices = tf.reshape(valid_indices, [-1])
  valid_dict = {}
  if fields.InputDataFields.groundtruth_boxes in tensor_dict:
    # Prevents reshape failure when num_boxes is 0.
    num_boxes = tf.maximum(tf.shape(
        tensor_dict[fields.InputDataFields.groundtruth_boxes])[0], 1)
    for key in tensor_dict:
      if key in [fields.InputDataFields.groundtruth_boxes,
                 fields.InputDataFields.groundtruth_classes,
                 fields.InputDataFields.groundtruth_confidences,
                 fields.InputDataFields.groundtruth_keypoints,
                 fields.InputDataFields.groundtruth_keypoint_visibilities,
                 fields.InputDataFields.groundtruth_instance_masks]:
        valid_dict[key] = tf.gather(tensor_dict[key], valid_indices)
      # Input decoder returns empty tensor when these fields are not provided.
      # Needs to reshape into [num_boxes, -1] for tf.gather() to work.
      elif key in [fields.InputDataFields.groundtruth_is_crowd,
                   fields.InputDataFields.groundtruth_area,
                   fields.InputDataFields.groundtruth_difficult,
                   fields.InputDataFields.groundtruth_label_types]:
        valid_dict[key] = tf.reshape(
            tf.gather(tf.reshape(tensor_dict[key], [num_boxes, -1]),
                      valid_indices), [-1])
      # Fields that are not associated with boxes.
      else:
        valid_dict[key] = tensor_dict[key]
  else:
    raise ValueError('%s not present in input tensor dict.' % (
        fields.InputDataFields.groundtruth_boxes))
  return valid_dict