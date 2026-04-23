def decode(self, tf_example_string_tensor):
    """Decodes serialized tensorflow example and returns a tensor dictionary.

    Args:
      tf_example_string_tensor: a string tensor holding a serialized tensorflow
        example proto.

    Returns:
      A dictionary of the following tensors.
      fields.InputDataFields.image - 3D uint8 tensor of shape [None, None, 3]
        containing image.
      fields.InputDataFields.original_image_spatial_shape - 1D int32 tensor of
        shape [2] containing shape of the image.
      fields.InputDataFields.source_id - string tensor containing original
        image id.
      fields.InputDataFields.key - string tensor with unique sha256 hash key.
      fields.InputDataFields.filename - string tensor with original dataset
        filename.
      fields.InputDataFields.groundtruth_boxes - 2D float32 tensor of shape
        [None, 4] containing box corners.
      fields.InputDataFields.groundtruth_classes - 1D int64 tensor of shape
        [None] containing classes for the boxes.
      fields.InputDataFields.groundtruth_weights - 1D float32 tensor of
        shape [None] indicating the weights of groundtruth boxes.
      fields.InputDataFields.groundtruth_area - 1D float32 tensor of shape
        [None] containing containing object mask area in pixel squared.
      fields.InputDataFields.groundtruth_is_crowd - 1D bool tensor of shape
        [None] indicating if the boxes enclose a crowd.

    Optional:
      fields.InputDataFields.groundtruth_image_confidences - 1D float tensor of
        shape [None] indicating if a class is present in the image (1.0) or
        a class is not present in the image (0.0).
      fields.InputDataFields.image_additional_channels - 3D uint8 tensor of
        shape [None, None, num_additional_channels]. 1st dim is height; 2nd dim
        is width; 3rd dim is the number of additional channels.
      fields.InputDataFields.groundtruth_difficult - 1D bool tensor of shape
        [None] indicating if the boxes represent `difficult` instances.
      fields.InputDataFields.groundtruth_group_of - 1D bool tensor of shape
        [None] indicating if the boxes represent `group_of` instances.
      fields.InputDataFields.groundtruth_keypoints - 3D float32 tensor of
        shape [None, num_keypoints, 2] containing keypoints, where the
        coordinates of the keypoints are ordered (y, x).
      fields.InputDataFields.groundtruth_keypoint_visibilities - 2D bool
        tensor of shape [None, num_keypoints] containing keypoint visibilites.
      fields.InputDataFields.groundtruth_instance_masks - 3D float32 tensor of
        shape [None, None, None] containing instance masks.
      fields.InputDataFields.groundtruth_instance_mask_weights - 1D float32
        tensor of shape [None] containing weights. These are typically values
        in {0.0, 1.0} which indicate whether to consider the mask related to an
        object.
      fields.InputDataFields.groundtruth_image_classes - 1D int64 of shape
        [None] containing classes for the boxes.
      fields.InputDataFields.multiclass_scores - 1D float32 tensor of shape
        [None * num_classes] containing flattened multiclass scores for
        groundtruth boxes.
      fields.InputDataFields.context_features - 1D float32 tensor of shape
        [context_feature_length * num_context_features]
      fields.InputDataFields.context_feature_length - int32 tensor specifying
        the length of each feature in context_features
    """
    serialized_example = tf.reshape(tf_example_string_tensor, shape=[])
    decoder = slim_example_decoder.TFExampleDecoder(self.keys_to_features,
                                                    self.items_to_handlers)
    keys = decoder.list_items()
    tensors = decoder.decode(serialized_example, items=keys)
    tensor_dict = dict(zip(keys, tensors))
    is_crowd = fields.InputDataFields.groundtruth_is_crowd
    tensor_dict[is_crowd] = tf.cast(tensor_dict[is_crowd], dtype=tf.bool)
    tensor_dict[fields.InputDataFields.image].set_shape([None, None, 3])
    tensor_dict[fields.InputDataFields.original_image_spatial_shape] = tf.shape(
        tensor_dict[fields.InputDataFields.image])[:2]

    if fields.InputDataFields.image_additional_channels in tensor_dict:
      channels = tensor_dict[fields.InputDataFields.image_additional_channels]
      channels = tf.squeeze(channels, axis=3)
      channels = tf.transpose(channels, perm=[1, 2, 0])
      tensor_dict[fields.InputDataFields.image_additional_channels] = channels

    def default_groundtruth_weights():
      return tf.ones(
          [tf.shape(tensor_dict[fields.InputDataFields.groundtruth_boxes])[0]],
          dtype=tf.float32)

    tensor_dict[fields.InputDataFields.groundtruth_weights] = tf.cond(
        tf.greater(
            tf.shape(
                tensor_dict[fields.InputDataFields.groundtruth_weights])[0],
            0), lambda: tensor_dict[fields.InputDataFields.groundtruth_weights],
        default_groundtruth_weights)

    if fields.InputDataFields.groundtruth_instance_masks in tensor_dict:
      gt_instance_masks = tensor_dict[
          fields.InputDataFields.groundtruth_instance_masks]
      num_gt_instance_masks = tf.shape(gt_instance_masks)[0]
      gt_instance_mask_weights = tensor_dict[
          fields.InputDataFields.groundtruth_instance_mask_weights]
      num_gt_instance_mask_weights = tf.shape(gt_instance_mask_weights)[0]
      def default_groundtruth_instance_mask_weights():
        return tf.ones([num_gt_instance_masks], dtype=tf.float32)

      tensor_dict[fields.InputDataFields.groundtruth_instance_mask_weights] = (
          tf.cond(tf.greater(num_gt_instance_mask_weights, 0),
                  lambda: gt_instance_mask_weights,
                  default_groundtruth_instance_mask_weights))

    if fields.InputDataFields.groundtruth_keypoints in tensor_dict:
      gt_kpt_fld = fields.InputDataFields.groundtruth_keypoints
      gt_kpt_vis_fld = fields.InputDataFields.groundtruth_keypoint_visibilities

      if self._keypoint_label_map is None:
        # Set all keypoints that are not labeled to NaN.
        tensor_dict[gt_kpt_fld] = tf.reshape(tensor_dict[gt_kpt_fld],
                                             [-1, self._num_keypoints, 2])
        tensor_dict[gt_kpt_vis_fld] = tf.reshape(
            tensor_dict[gt_kpt_vis_fld], [-1, self._num_keypoints])
        visibilities_tiled = tf.tile(
            tf.expand_dims(tensor_dict[gt_kpt_vis_fld], axis=-1), [1, 1, 2])
        tensor_dict[gt_kpt_fld] = tf.where(
            visibilities_tiled, tensor_dict[gt_kpt_fld],
            np.nan * tf.ones_like(tensor_dict[gt_kpt_fld]))
      else:
        num_instances = tf.shape(tensor_dict['groundtruth_classes'])[0]
        def true_fn(num_instances):
          """Logics to process the tensor when num_instances is not zero."""
          kpts_idx = tf.cast(self._kpts_name_to_id_table.lookup(
              tensor_dict[_KEYPOINT_TEXT_FIELD]), dtype=tf.int32)
          num_kpt_texts = tf.cast(
              tf.size(tensor_dict[_KEYPOINT_TEXT_FIELD]) / num_instances,
              dtype=tf.int32)
          # Prepare the index of the instances: [num_instances, num_kpt_texts].
          instance_idx = tf.tile(
              tf.expand_dims(tf.range(num_instances, dtype=tf.int32), axis=-1),
              [1, num_kpt_texts])
          # Prepare the index of the keypoints to scatter the keypoint
          # coordinates: [num_kpts_texts * num_instances, 2].
          full_kpt_idx = tf.concat([
              tf.reshape(
                  instance_idx, shape=[num_kpt_texts * num_instances, 1]),
              tf.expand_dims(kpts_idx, axis=-1)
          ], axis=1)

          # Get the mask and gather only the keypoints with non-negative
          # indices (i.e. the keypoint labels in the image/object/keypoint/text
          # but do not exist in the label map).
          valid_mask = tf.greater_equal(kpts_idx, 0)
          full_kpt_idx = tf.boolean_mask(full_kpt_idx, valid_mask)

          gt_kpt = tf.scatter_nd(
              full_kpt_idx,
              tf.boolean_mask(tensor_dict[gt_kpt_fld], valid_mask),
              shape=[num_instances, self._num_keypoints, 2])
          gt_kpt_vis = tf.cast(tf.scatter_nd(
              full_kpt_idx,
              tf.boolean_mask(tensor_dict[gt_kpt_vis_fld], valid_mask),
              shape=[num_instances, self._num_keypoints]), dtype=tf.bool)
          visibilities_tiled = tf.tile(
              tf.expand_dims(gt_kpt_vis, axis=-1), [1, 1, 2])
          gt_kpt = tf.where(visibilities_tiled, gt_kpt,
                            np.nan * tf.ones_like(gt_kpt))
          return (gt_kpt, gt_kpt_vis)

        def false_fn():
          """Logics to process the tensor when num_instances is zero."""
          return (tf.zeros([0, self._num_keypoints, 2], dtype=tf.float32),
                  tf.zeros([0, self._num_keypoints], dtype=tf.bool))

        true_fn = functools.partial(true_fn, num_instances)
        results = tf.cond(num_instances > 0, true_fn, false_fn)

        tensor_dict[gt_kpt_fld] = results[0]
        tensor_dict[gt_kpt_vis_fld] = results[1]
        # Since the keypoint text tensor won't be used anymore, deleting it from
        # the tensor_dict to avoid further code changes to handle it in the
        # inputs.py file.
        del tensor_dict[_KEYPOINT_TEXT_FIELD]

    if self._expand_hierarchy_labels:
      input_fields = fields.InputDataFields
      image_classes, image_confidences = self._expand_image_label_hierarchy(
          tensor_dict[input_fields.groundtruth_image_classes],
          tensor_dict[input_fields.groundtruth_image_confidences])
      tensor_dict[input_fields.groundtruth_image_classes] = image_classes
      tensor_dict[input_fields.groundtruth_image_confidences] = (
          image_confidences)

      box_fields = [
          fields.InputDataFields.groundtruth_group_of,
          fields.InputDataFields.groundtruth_is_crowd,
          fields.InputDataFields.groundtruth_difficult,
          fields.InputDataFields.groundtruth_area,
          fields.InputDataFields.groundtruth_boxes,
          fields.InputDataFields.groundtruth_weights,
      ]

      def expand_field(field_name):
        return self._expansion_box_field_labels(
            tensor_dict[input_fields.groundtruth_classes],
            tensor_dict[field_name])

      # pylint: disable=cell-var-from-loop
      for field in box_fields:
        if field in tensor_dict:
          tensor_dict[field] = tf.cond(
              tf.size(tensor_dict[field]) > 0, lambda: expand_field(field),
              lambda: tensor_dict[field])
      # pylint: enable=cell-var-from-loop

      tensor_dict[input_fields.groundtruth_classes] = (
          self._expansion_box_field_labels(
              tensor_dict[input_fields.groundtruth_classes],
              tensor_dict[input_fields.groundtruth_classes], True))

    if fields.InputDataFields.groundtruth_group_of in tensor_dict:
      group_of = fields.InputDataFields.groundtruth_group_of
      tensor_dict[group_of] = tf.cast(tensor_dict[group_of], dtype=tf.bool)

    if fields.InputDataFields.groundtruth_dp_num_points in tensor_dict:
      tensor_dict[fields.InputDataFields.groundtruth_dp_num_points] = tf.cast(
          tensor_dict[fields.InputDataFields.groundtruth_dp_num_points],
          dtype=tf.int32)
      tensor_dict[fields.InputDataFields.groundtruth_dp_part_ids] = tf.cast(
          tensor_dict[fields.InputDataFields.groundtruth_dp_part_ids],
          dtype=tf.int32)

    if fields.InputDataFields.groundtruth_track_ids in tensor_dict:
      tensor_dict[fields.InputDataFields.groundtruth_track_ids] = tf.cast(
          tensor_dict[fields.InputDataFields.groundtruth_track_ids],
          dtype=tf.int32)

    return tensor_dict