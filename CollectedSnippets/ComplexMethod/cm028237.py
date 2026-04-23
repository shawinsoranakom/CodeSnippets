def __init__(self,
               load_instance_masks=False,
               instance_mask_type=input_reader_pb2.NUMERICAL_MASKS,
               label_map_proto_file=None,
               use_display_name=False,
               dct_method='',
               num_keypoints=0,
               num_additional_channels=0,
               load_multiclass_scores=False,
               load_context_features=False,
               expand_hierarchy_labels=False,
               load_dense_pose=False,
               load_track_id=False,
               load_keypoint_depth_features=False,
               use_keypoint_label_map=False):
    """Constructor sets keys_to_features and items_to_handlers.

    Args:
      load_instance_masks: whether or not to load and handle instance masks.
      instance_mask_type: type of instance masks. Options are provided in
        input_reader.proto. This is only used if `load_instance_masks` is True.
      label_map_proto_file: a file path to a
        object_detection.protos.StringIntLabelMap proto. If provided, then the
        mapped IDs of 'image/object/class/text' will take precedence over the
        existing 'image/object/class/label' ID.  Also, if provided, it is
        assumed that 'image/object/class/text' will be in the data.
      use_display_name: whether or not to use the `display_name` for label
        mapping (instead of `name`).  Only used if label_map_proto_file is
        provided.
      dct_method: An optional string. Defaults to None. It only takes
        effect when image format is jpeg, used to specify a hint about the
        algorithm used for jpeg decompression. Currently valid values
        are ['INTEGER_FAST', 'INTEGER_ACCURATE']. The hint may be ignored, for
        example, the jpeg library does not have that specific option.
      num_keypoints: the number of keypoints per object.
      num_additional_channels: how many additional channels to use.
      load_multiclass_scores: Whether to load multiclass scores associated with
        boxes.
      load_context_features: Whether to load information from context_features,
        to provide additional context to a detection model for training and/or
        inference.
      expand_hierarchy_labels: Expands the object and image labels taking into
        account the provided hierarchy in the label_map_proto_file. For positive
        classes, the labels are extended to ancestor. For negative classes,
        the labels are expanded to descendants.
      load_dense_pose: Whether to load DensePose annotations.
      load_track_id: Whether to load tracking annotations.
      load_keypoint_depth_features: Whether to load the keypoint depth features
        including keypoint relative depths and weights. If this field is set to
        True but no keypoint depth features are in the input tf.Example, then
        default values will be populated.
      use_keypoint_label_map: If set to True, the 'image/object/keypoint/text'
        field will be used to map the keypoint coordinates (using the label
        map defined in label_map_proto_file) instead of assuming the ordering
        in the tf.Example feature. This is useful when training with multiple
        datasets while each of them contains different subset of keypoint
        annotations.

    Raises:
      ValueError: If `instance_mask_type` option is not one of
        input_reader_pb2.DEFAULT, input_reader_pb2.NUMERICAL, or
        input_reader_pb2.PNG_MASKS.
      ValueError: If `expand_labels_hierarchy` is True, but the
        `label_map_proto_file` is not provided.
    """

    # TODO(rathodv): delete unused `use_display_name` argument once we change
    # other decoders to handle label maps similarly.
    del use_display_name
    self.keys_to_features = {
        'image/encoded':
            tf.FixedLenFeature((), tf.string, default_value=''),
        'image/format':
            tf.FixedLenFeature((), tf.string, default_value='jpeg'),
        'image/filename':
            tf.FixedLenFeature((), tf.string, default_value=''),
        'image/key/sha256':
            tf.FixedLenFeature((), tf.string, default_value=''),
        'image/source_id':
            tf.FixedLenFeature((), tf.string, default_value=''),
        'image/height':
            tf.FixedLenFeature((), tf.int64, default_value=1),
        'image/width':
            tf.FixedLenFeature((), tf.int64, default_value=1),
        # Image-level labels.
        'image/class/text':
            tf.VarLenFeature(tf.string),
        'image/class/label':
            tf.VarLenFeature(tf.int64),
        'image/neg_category_ids':
            tf.VarLenFeature(tf.int64),
        'image/not_exhaustive_category_ids':
            tf.VarLenFeature(tf.int64),
        'image/class/confidence':
            tf.VarLenFeature(tf.float32),
        # Object boxes and classes.
        'image/object/bbox/xmin':
            tf.VarLenFeature(tf.float32),
        'image/object/bbox/xmax':
            tf.VarLenFeature(tf.float32),
        'image/object/bbox/ymin':
            tf.VarLenFeature(tf.float32),
        'image/object/bbox/ymax':
            tf.VarLenFeature(tf.float32),
        'image/object/class/label':
            tf.VarLenFeature(tf.int64),
        'image/object/class/text':
            tf.VarLenFeature(tf.string),
        'image/object/area':
            tf.VarLenFeature(tf.float32),
        'image/object/is_crowd':
            tf.VarLenFeature(tf.int64),
        'image/object/difficult':
            tf.VarLenFeature(tf.int64),
        'image/object/group_of':
            tf.VarLenFeature(tf.int64),
        'image/object/weight':
            tf.VarLenFeature(tf.float32),

    }
    # We are checking `dct_method` instead of passing it directly in order to
    # ensure TF version 1.6 compatibility.
    if dct_method:
      image = slim_example_decoder.Image(
          image_key='image/encoded',
          format_key='image/format',
          channels=3,
          dct_method=dct_method)
      additional_channel_image = slim_example_decoder.Image(
          image_key='image/additional_channels/encoded',
          format_key='image/format',
          channels=1,
          repeated=True,
          dct_method=dct_method)
    else:
      image = slim_example_decoder.Image(
          image_key='image/encoded', format_key='image/format', channels=3)
      additional_channel_image = slim_example_decoder.Image(
          image_key='image/additional_channels/encoded',
          format_key='image/format',
          channels=1,
          repeated=True)
    self.items_to_handlers = {
        fields.InputDataFields.image:
            image,
        fields.InputDataFields.source_id: (
            slim_example_decoder.Tensor('image/source_id')),
        fields.InputDataFields.key: (
            slim_example_decoder.Tensor('image/key/sha256')),
        fields.InputDataFields.filename: (
            slim_example_decoder.Tensor('image/filename')),
        # Image-level labels.
        fields.InputDataFields.groundtruth_image_confidences: (
            slim_example_decoder.Tensor('image/class/confidence')),
        fields.InputDataFields.groundtruth_verified_neg_classes: (
            slim_example_decoder.Tensor('image/neg_category_ids')),
        fields.InputDataFields.groundtruth_not_exhaustive_classes: (
            slim_example_decoder.Tensor('image/not_exhaustive_category_ids')),
        # Object boxes and classes.
        fields.InputDataFields.groundtruth_boxes: (
            slim_example_decoder.BoundingBox(['ymin', 'xmin', 'ymax', 'xmax'],
                                             'image/object/bbox/')),
        fields.InputDataFields.groundtruth_area:
            slim_example_decoder.Tensor('image/object/area'),
        fields.InputDataFields.groundtruth_is_crowd: (
            slim_example_decoder.Tensor('image/object/is_crowd')),
        fields.InputDataFields.groundtruth_difficult: (
            slim_example_decoder.Tensor('image/object/difficult')),
        fields.InputDataFields.groundtruth_group_of: (
            slim_example_decoder.Tensor('image/object/group_of')),
        fields.InputDataFields.groundtruth_weights: (
            slim_example_decoder.Tensor('image/object/weight')),

    }

    self._keypoint_label_map = None
    if use_keypoint_label_map:
      assert label_map_proto_file is not None
      self._keypoint_label_map = label_map_util.get_keypoint_label_map_dict(
          label_map_proto_file)
      # We use a default_value of -1, but we expect all labels to be
      # contained in the label map.
      try:
        # Dynamically try to load the tf v2 lookup, falling back to contrib
        lookup = tf.compat.v2.lookup
        hash_table_class = tf.compat.v2.lookup.StaticHashTable
      except AttributeError:
        lookup = contrib_lookup
        hash_table_class = contrib_lookup.HashTable
      self._kpts_name_to_id_table = hash_table_class(
          initializer=lookup.KeyValueTensorInitializer(
              keys=tf.constant(list(self._keypoint_label_map.keys())),
              values=tf.constant(
                  list(self._keypoint_label_map.values()), dtype=tf.int64)),
          default_value=-1)

      self.keys_to_features[_KEYPOINT_TEXT_FIELD] = tf.VarLenFeature(
          tf.string)
      self.items_to_handlers[_KEYPOINT_TEXT_FIELD] = (
          slim_example_decoder.ItemHandlerCallback(
              [_KEYPOINT_TEXT_FIELD], self._keypoint_text_handle))

    if load_multiclass_scores:
      self.keys_to_features[
          'image/object/class/multiclass_scores'] = tf.VarLenFeature(tf.float32)
      self.items_to_handlers[fields.InputDataFields.multiclass_scores] = (
          slim_example_decoder.Tensor('image/object/class/multiclass_scores'))

    if load_context_features:
      self.keys_to_features[
          'image/context_features'] = tf.VarLenFeature(tf.float32)
      self.items_to_handlers[fields.InputDataFields.context_features] = (
          slim_example_decoder.ItemHandlerCallback(
              ['image/context_features', 'image/context_feature_length'],
              self._reshape_context_features))

      self.keys_to_features[
          'image/context_feature_length'] = tf.FixedLenFeature((), tf.int64)
      self.items_to_handlers[fields.InputDataFields.context_feature_length] = (
          slim_example_decoder.Tensor('image/context_feature_length'))

    if num_additional_channels > 0:
      self.keys_to_features[
          'image/additional_channels/encoded'] = tf.FixedLenFeature(
              (num_additional_channels,), tf.string)
      self.items_to_handlers[
          fields.InputDataFields.
          image_additional_channels] = additional_channel_image
    self._num_keypoints = num_keypoints
    if num_keypoints > 0:
      self.keys_to_features['image/object/keypoint/x'] = (
          tf.VarLenFeature(tf.float32))
      self.keys_to_features['image/object/keypoint/y'] = (
          tf.VarLenFeature(tf.float32))
      self.keys_to_features['image/object/keypoint/visibility'] = (
          tf.VarLenFeature(tf.int64))
      self.items_to_handlers[fields.InputDataFields.groundtruth_keypoints] = (
          slim_example_decoder.ItemHandlerCallback(
              ['image/object/keypoint/y', 'image/object/keypoint/x'],
              self._reshape_keypoints))
      kpt_vis_field = fields.InputDataFields.groundtruth_keypoint_visibilities
      self.items_to_handlers[kpt_vis_field] = (
          slim_example_decoder.ItemHandlerCallback(
              ['image/object/keypoint/x', 'image/object/keypoint/visibility'],
              self._reshape_keypoint_visibilities))
      if load_keypoint_depth_features:
        self.keys_to_features['image/object/keypoint/z'] = (
            tf.VarLenFeature(tf.float32))
        self.keys_to_features['image/object/keypoint/z/weights'] = (
            tf.VarLenFeature(tf.float32))
        self.items_to_handlers[
            fields.InputDataFields.groundtruth_keypoint_depths] = (
                slim_example_decoder.ItemHandlerCallback(
                    ['image/object/keypoint/x', 'image/object/keypoint/z'],
                    self._reshape_keypoint_depths))
        self.items_to_handlers[
            fields.InputDataFields.groundtruth_keypoint_depth_weights] = (
                slim_example_decoder.ItemHandlerCallback(
                    ['image/object/keypoint/x',
                     'image/object/keypoint/z/weights'],
                    self._reshape_keypoint_depth_weights))

    if load_instance_masks:
      if instance_mask_type in (input_reader_pb2.DEFAULT,
                                input_reader_pb2.NUMERICAL_MASKS):
        self.keys_to_features['image/object/mask'] = (
            tf.VarLenFeature(tf.float32))
        self.items_to_handlers[
            fields.InputDataFields.groundtruth_instance_masks] = (
                slim_example_decoder.ItemHandlerCallback(
                    ['image/object/mask', 'image/height', 'image/width'],
                    self._reshape_instance_masks))
      elif instance_mask_type == input_reader_pb2.PNG_MASKS:
        self.keys_to_features['image/object/mask'] = tf.VarLenFeature(tf.string)
        self.items_to_handlers[
            fields.InputDataFields.groundtruth_instance_masks] = (
                slim_example_decoder.ItemHandlerCallback(
                    ['image/object/mask', 'image/height', 'image/width'],
                    self._decode_png_instance_masks))
      else:
        raise ValueError('Did not recognize the `instance_mask_type` option.')
      self.keys_to_features['image/object/mask/weight'] = (
          tf.VarLenFeature(tf.float32))
      self.items_to_handlers[
          fields.InputDataFields.groundtruth_instance_mask_weights] = (
              slim_example_decoder.Tensor('image/object/mask/weight'))
    if load_dense_pose:
      self.keys_to_features['image/object/densepose/num'] = (
          tf.VarLenFeature(tf.int64))
      self.keys_to_features['image/object/densepose/part_index'] = (
          tf.VarLenFeature(tf.int64))
      self.keys_to_features['image/object/densepose/x'] = (
          tf.VarLenFeature(tf.float32))
      self.keys_to_features['image/object/densepose/y'] = (
          tf.VarLenFeature(tf.float32))
      self.keys_to_features['image/object/densepose/u'] = (
          tf.VarLenFeature(tf.float32))
      self.keys_to_features['image/object/densepose/v'] = (
          tf.VarLenFeature(tf.float32))
      self.items_to_handlers[
          fields.InputDataFields.groundtruth_dp_num_points] = (
              slim_example_decoder.Tensor('image/object/densepose/num'))
      self.items_to_handlers[fields.InputDataFields.groundtruth_dp_part_ids] = (
          slim_example_decoder.ItemHandlerCallback(
              ['image/object/densepose/part_index',
               'image/object/densepose/num'], self._dense_pose_part_indices))
      self.items_to_handlers[
          fields.InputDataFields.groundtruth_dp_surface_coords] = (
              slim_example_decoder.ItemHandlerCallback(
                  ['image/object/densepose/x', 'image/object/densepose/y',
                   'image/object/densepose/u', 'image/object/densepose/v',
                   'image/object/densepose/num'],
                  self._dense_pose_surface_coordinates))
    if load_track_id:
      self.keys_to_features['image/object/track/label'] = (
          tf.VarLenFeature(tf.int64))
      self.items_to_handlers[
          fields.InputDataFields.groundtruth_track_ids] = (
              slim_example_decoder.Tensor('image/object/track/label'))

    if label_map_proto_file:
      # If the label_map_proto is provided, try to use it in conjunction with
      # the class text, and fall back to a materialized ID.
      label_handler = slim_example_decoder.BackupHandler(
          _ClassTensorHandler(
              'image/object/class/text', label_map_proto_file,
              default_value=''),
          slim_example_decoder.Tensor('image/object/class/label'))
      image_label_handler = slim_example_decoder.BackupHandler(
          _ClassTensorHandler(
              fields.TfExampleFields.image_class_text,
              label_map_proto_file,
              default_value=''),
          slim_example_decoder.Tensor(fields.TfExampleFields.image_class_label))
    else:
      label_handler = slim_example_decoder.Tensor('image/object/class/label')
      image_label_handler = slim_example_decoder.Tensor(
          fields.TfExampleFields.image_class_label)
    self.items_to_handlers[
        fields.InputDataFields.groundtruth_classes] = label_handler
    self.items_to_handlers[
        fields.InputDataFields.groundtruth_image_classes] = image_label_handler

    self._expand_hierarchy_labels = expand_hierarchy_labels
    self._ancestors_lut = None
    self._descendants_lut = None
    if expand_hierarchy_labels:
      if label_map_proto_file:
        ancestors_lut, descendants_lut = (
            label_map_util.get_label_map_hierarchy_lut(label_map_proto_file,
                                                       True))
        self._ancestors_lut = tf.constant(ancestors_lut, dtype=tf.int64)
        self._descendants_lut = tf.constant(descendants_lut, dtype=tf.int64)
      else:
        raise ValueError('In order to expand labels, the label_map_proto_file '
                         'has to be provided.')