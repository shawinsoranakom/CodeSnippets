def pad_input_data_to_static_shapes(tensor_dict,
                                    max_num_boxes,
                                    num_classes,
                                    spatial_image_shape=None,
                                    max_num_context_features=None,
                                    context_feature_length=None,
                                    max_dp_points=336):
  """Pads input tensors to static shapes.

  In case num_additional_channels > 0, we assume that the additional channels
  have already been concatenated to the base image.

  Args:
    tensor_dict: Tensor dictionary of input data
    max_num_boxes: Max number of groundtruth boxes needed to compute shapes for
      padding.
    num_classes: Number of classes in the dataset needed to compute shapes for
      padding.
    spatial_image_shape: A list of two integers of the form [height, width]
      containing expected spatial shape of the image.
    max_num_context_features (optional): The maximum number of context
      features needed to compute shapes padding.
    context_feature_length (optional): The length of the context feature.
    max_dp_points (optional): The maximum number of DensePose sampled points per
      instance. The default (336) is selected since the original DensePose paper
      (https://arxiv.org/pdf/1802.00434.pdf) indicates that the maximum number
      of samples per part is 14, and therefore 24 * 14 = 336 is the maximum
      sampler per instance.

  Returns:
    A dictionary keyed by fields.InputDataFields containing padding shapes for
    tensors in the dataset.

  Raises:
    ValueError: If groundtruth classes is neither rank 1 nor rank 2, or if we
      detect that additional channels have not been concatenated yet, or if
      max_num_context_features is not specified and context_features is in the
      tensor dict.
  """
  if not spatial_image_shape or spatial_image_shape == [-1, -1]:
    height, width = None, None
  else:
    height, width = spatial_image_shape  # pylint: disable=unpacking-non-sequence

  input_fields = fields.InputDataFields
  num_additional_channels = 0
  if input_fields.image_additional_channels in tensor_dict:
    num_additional_channels = shape_utils.get_dim_as_int(tensor_dict[
        input_fields.image_additional_channels].shape[2])

  # We assume that if num_additional_channels > 0, then it has already been
  # concatenated to the base image (but not the ground truth).
  num_channels = 3
  if input_fields.image in tensor_dict:
    num_channels = shape_utils.get_dim_as_int(
        tensor_dict[input_fields.image].shape[2])

  if num_additional_channels:
    if num_additional_channels >= num_channels:
      raise ValueError(
          'Image must be already concatenated with additional channels.')

    if (input_fields.original_image in tensor_dict and
        shape_utils.get_dim_as_int(
            tensor_dict[input_fields.original_image].shape[2]) ==
        num_channels):
      raise ValueError(
          'Image must be already concatenated with additional channels.')

  if input_fields.context_features in tensor_dict and (
      max_num_context_features is None):
    raise ValueError('max_num_context_features must be specified in the model '
                     'config if include_context is specified in the input '
                     'config')

  padding_shapes = {
      input_fields.image: [height, width, num_channels],
      input_fields.original_image_spatial_shape: [2],
      input_fields.image_additional_channels: [
          height, width, num_additional_channels
      ],
      input_fields.source_id: [],
      input_fields.filename: [],
      input_fields.key: [],
      input_fields.groundtruth_difficult: [max_num_boxes],
      input_fields.groundtruth_boxes: [max_num_boxes, 4],
      input_fields.groundtruth_classes: [max_num_boxes, num_classes],
      input_fields.groundtruth_instance_masks: [
          max_num_boxes, height, width
      ],
      input_fields.groundtruth_instance_mask_weights: [max_num_boxes],
      input_fields.groundtruth_is_crowd: [max_num_boxes],
      input_fields.groundtruth_group_of: [max_num_boxes],
      input_fields.groundtruth_area: [max_num_boxes],
      input_fields.groundtruth_weights: [max_num_boxes],
      input_fields.groundtruth_confidences: [
          max_num_boxes, num_classes
      ],
      input_fields.num_groundtruth_boxes: [],
      input_fields.groundtruth_label_types: [max_num_boxes],
      input_fields.groundtruth_label_weights: [max_num_boxes],
      input_fields.true_image_shape: [3],
      input_fields.groundtruth_image_classes: [num_classes],
      input_fields.groundtruth_image_confidences: [num_classes],
      input_fields.groundtruth_labeled_classes: [num_classes],
  }

  if input_fields.original_image in tensor_dict:
    padding_shapes[input_fields.original_image] = [
        height, width,
        shape_utils.get_dim_as_int(tensor_dict[input_fields.
                                               original_image].shape[2])
    ]
  if input_fields.groundtruth_keypoints in tensor_dict:
    tensor_shape = (
        tensor_dict[input_fields.groundtruth_keypoints].shape)
    padding_shape = [max_num_boxes,
                     shape_utils.get_dim_as_int(tensor_shape[1]),
                     shape_utils.get_dim_as_int(tensor_shape[2])]
    padding_shapes[input_fields.groundtruth_keypoints] = padding_shape
  if input_fields.groundtruth_keypoint_visibilities in tensor_dict:
    tensor_shape = tensor_dict[input_fields.
                               groundtruth_keypoint_visibilities].shape
    padding_shape = [max_num_boxes, shape_utils.get_dim_as_int(tensor_shape[1])]
    padding_shapes[input_fields.
                   groundtruth_keypoint_visibilities] = padding_shape

  if fields.InputDataFields.groundtruth_keypoint_depths in tensor_dict:
    tensor_shape = tensor_dict[fields.InputDataFields.
                               groundtruth_keypoint_depths].shape
    padding_shape = [max_num_boxes, shape_utils.get_dim_as_int(tensor_shape[1])]
    padding_shapes[fields.InputDataFields.
                   groundtruth_keypoint_depths] = padding_shape
    padding_shapes[fields.InputDataFields.
                   groundtruth_keypoint_depth_weights] = padding_shape

  if input_fields.groundtruth_keypoint_weights in tensor_dict:
    tensor_shape = (
        tensor_dict[input_fields.groundtruth_keypoint_weights].shape)
    padding_shape = [max_num_boxes, shape_utils.get_dim_as_int(tensor_shape[1])]
    padding_shapes[input_fields.
                   groundtruth_keypoint_weights] = padding_shape
  if input_fields.groundtruth_dp_num_points in tensor_dict:
    padding_shapes[
        input_fields.groundtruth_dp_num_points] = [max_num_boxes]
    padding_shapes[
        input_fields.groundtruth_dp_part_ids] = [
            max_num_boxes, max_dp_points]
    padding_shapes[
        input_fields.groundtruth_dp_surface_coords] = [
            max_num_boxes, max_dp_points, 4]
  if input_fields.groundtruth_track_ids in tensor_dict:
    padding_shapes[
        input_fields.groundtruth_track_ids] = [max_num_boxes]

  if input_fields.groundtruth_verified_neg_classes in tensor_dict:
    padding_shapes[
        input_fields.groundtruth_verified_neg_classes] = [num_classes]
  if input_fields.groundtruth_not_exhaustive_classes in tensor_dict:
    padding_shapes[
        input_fields.groundtruth_not_exhaustive_classes] = [num_classes]

  # Prepare for ContextRCNN related fields.
  if input_fields.context_features in tensor_dict:
    padding_shape = [max_num_context_features, context_feature_length]
    padding_shapes[input_fields.context_features] = padding_shape

    tensor_shape = tf.shape(
        tensor_dict[fields.InputDataFields.context_features])
    tensor_dict[fields.InputDataFields.valid_context_size] = tensor_shape[0]
    padding_shapes[fields.InputDataFields.valid_context_size] = []
  if fields.InputDataFields.context_feature_length in tensor_dict:
    padding_shapes[fields.InputDataFields.context_feature_length] = []
  if fields.InputDataFields.context_features_image_id_list in tensor_dict:
    padding_shapes[fields.InputDataFields.context_features_image_id_list] = [
        max_num_context_features]

  if input_fields.is_annotated in tensor_dict:
    padding_shapes[input_fields.is_annotated] = []

  padded_tensor_dict = {}
  for tensor_name in tensor_dict:
    padded_tensor_dict[tensor_name] = shape_utils.pad_or_clip_nd(
        tensor_dict[tensor_name], padding_shapes[tensor_name])

  # Make sure that the number of groundtruth boxes now reflects the
  # padded/clipped tensors.
  if input_fields.num_groundtruth_boxes in padded_tensor_dict:
    padded_tensor_dict[input_fields.num_groundtruth_boxes] = (
        tf.minimum(
            padded_tensor_dict[input_fields.num_groundtruth_boxes],
            max_num_boxes))
  return padded_tensor_dict