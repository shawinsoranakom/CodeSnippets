def unstack_batch(tensor_dict, unpad_groundtruth_tensors=True):
  """Unstacks all tensors in `tensor_dict` along 0th dimension.

  Unstacks tensor from the tensor dict along 0th dimension and returns a
  tensor_dict containing values that are lists of unstacked, unpadded tensors.

  Tensors in the `tensor_dict` are expected to be of one of the three shapes:
  1. [batch_size]
  2. [batch_size, height, width, channels]
  3. [batch_size, num_boxes, d1, d2, ... dn]

  When unpad_groundtruth_tensors is set to true, unstacked tensors of form 3
  above are sliced along the `num_boxes` dimension using the value in tensor
  field.InputDataFields.num_groundtruth_boxes.

  Note that this function has a static list of input data fields and has to be
  kept in sync with the InputDataFields defined in core/standard_fields.py

  Args:
    tensor_dict: A dictionary of batched groundtruth tensors.
    unpad_groundtruth_tensors: Whether to remove padding along `num_boxes`
      dimension of the groundtruth tensors.

  Returns:
    A dictionary where the keys are from fields.InputDataFields and values are
    a list of unstacked (optionally unpadded) tensors.

  Raises:
    ValueError: If unpad_tensors is True and `tensor_dict` does not contain
      `num_groundtruth_boxes` tensor.
  """
  unbatched_tensor_dict = {
      key: tf.unstack(tensor) for key, tensor in tensor_dict.items()
  }
  if unpad_groundtruth_tensors:
    if (fields.InputDataFields.num_groundtruth_boxes
        not in unbatched_tensor_dict):
      raise ValueError('`num_groundtruth_boxes` not found in tensor_dict. '
                       'Keys available: {}'.format(
                           unbatched_tensor_dict.keys()))
    unbatched_unpadded_tensor_dict = {}
    unpad_keys = set([
        # List of input data fields that are padded along the num_boxes
        # dimension. This list has to be kept in sync with InputDataFields in
        # standard_fields.py.
        fields.InputDataFields.groundtruth_instance_masks,
        fields.InputDataFields.groundtruth_instance_mask_weights,
        fields.InputDataFields.groundtruth_classes,
        fields.InputDataFields.groundtruth_boxes,
        fields.InputDataFields.groundtruth_keypoints,
        fields.InputDataFields.groundtruth_keypoint_depths,
        fields.InputDataFields.groundtruth_keypoint_depth_weights,
        fields.InputDataFields.groundtruth_keypoint_visibilities,
        fields.InputDataFields.groundtruth_dp_num_points,
        fields.InputDataFields.groundtruth_dp_part_ids,
        fields.InputDataFields.groundtruth_dp_surface_coords,
        fields.InputDataFields.groundtruth_track_ids,
        fields.InputDataFields.groundtruth_group_of,
        fields.InputDataFields.groundtruth_difficult,
        fields.InputDataFields.groundtruth_is_crowd,
        fields.InputDataFields.groundtruth_area,
        fields.InputDataFields.groundtruth_weights
    ]).intersection(set(unbatched_tensor_dict.keys()))

    for key in unpad_keys:
      unpadded_tensor_list = []
      for num_gt, padded_tensor in zip(
          unbatched_tensor_dict[fields.InputDataFields.num_groundtruth_boxes],
          unbatched_tensor_dict[key]):
        tensor_shape = shape_utils.combined_static_and_dynamic_shape(
            padded_tensor)
        slice_begin = tf.zeros([len(tensor_shape)], dtype=tf.int32)
        slice_size = tf.stack(
            [num_gt] + [-1 if dim is None else dim for dim in tensor_shape[1:]])
        unpadded_tensor = tf.slice(padded_tensor, slice_begin, slice_size)
        unpadded_tensor_list.append(unpadded_tensor)
      unbatched_unpadded_tensor_dict[key] = unpadded_tensor_list

    unbatched_tensor_dict.update(unbatched_unpadded_tensor_dict)

  return unbatched_tensor_dict