def add_context_label(
    parser_builder: builders.SequenceExampleParserBuilder,
    sampler_builder: builders.SamplerBuilder,
    preprocessor_builder: builders.PreprocessorBuilder,
    input_label_index_feature_name: str = 'clip/key_frame/bbox/label/index',
    output_label_index_feature_name: str = builders.LABEL_INDEX_FEATURE_NAME,
    input_label_name_feature_name: str = 'clip/key_frame/bbox/label/string',
    output_label_name_feature_name: str = builders.LABEL_NAME_FEATURE_NAME,
    # Label related parameters.
    num_frames: int = 1,
    num_instances_per_frame: int = 5,
    zero_based_index: bool = False,
    one_hot_label: bool = True,
    num_classes: Optional[int] = None,
    add_label_name: bool = False):
  """Adds functions to process label feature to builders.

  Args:
    parser_builder: An instance of a builders.SequenceExampleParserBuilder.
    sampler_builder: An instance of a builders.SamplerBuilder.
    preprocessor_builder: An instance of a builders.PreprocessorBuilder.
    input_label_index_feature_name: Name of the label index feature in the input
      SequenceExample. Exposing this as an argument allows using this function
      for different label features.
    output_label_index_feature_name: Name of the label index feature in the
      output features dictionary. Exposing this as an argument allows using this
      function for different label features.
    input_label_name_feature_name: Name of the label name feature in the input
      SequenceExample. Exposing this as an argument allows using this function
      for different label features.
    output_label_name_feature_name: Name of the label name feature in the
      output features dictionary. Exposing this as an argument allows using this
      function for different label features.
    num_frames: The number of frames. If the num_frames > 1, the labels will be
      duplicated.
    num_instances_per_frame: The number of label instances per frames.
    zero_based_index: Whether the raw index are zero based. If not, converted to
      the zero based index as the output.
    one_hot_label: Return labels as one hot tensors. If is_multi_label is True,
      one hot tensor might have multiple ones.
    num_classes: Total number of classes in the dataset. It has to be procided
      if one_hot_label is True.
    add_label_name: Also return the name of the label. Not yet supported for
      multi label.
  """
  # Validate parameters.
  if one_hot_label and not num_classes:
    raise ValueError(
        'num_classes should be given when requesting one hot label.')

  # Parse label.
  parser_builder.parse_feature(
      feature_name=input_label_index_feature_name,
      feature_type=tf.io.VarLenFeature(dtype=tf.int64),
      output_name=output_label_index_feature_name,
      is_context=True)

  # Densify labels tensor in order to support multi label case.
  sampler_builder.add_fn(
      fn=lambda x: tf.sparse.to_dense(x, default_value=-1),
      feature_name=output_label_index_feature_name,
      fn_name='{}_sparse_to_dense'.format(output_label_index_feature_name))

  # Crop or pad labels to max_num_instance.
  crop_or_pad_features_fn = functools.partial(
      processors.crop_or_pad_features,
      max_num_features=num_instances_per_frame,
      feature_dimension=1,
      constant_values=-1)
  preprocessor_builder.add_fn(
      fn=crop_or_pad_features_fn,
      feature_name=output_label_index_feature_name,
      fn_name='{}_crop_or_pad'.format(output_label_index_feature_name))

  if num_frames > 1:
    preprocessor_builder.add_fn(
        fn=lambda x: tf.tile(x, [num_frames, 1]),
        feature_name=output_label_index_feature_name,
        fn_name='{}_duplicate'.format(output_label_index_feature_name))

  # Reshape the feature vector in [T, N].
  target_shape = [num_frames, num_instances_per_frame]
  preprocessor_builder.add_fn(
      fn=lambda x: tf.reshape(x, target_shape),
      feature_name=output_label_index_feature_name,
      fn_name='{}_reshape'.format(output_label_index_feature_name))

  # Convert the label id to be zero-indexed.
  if not zero_based_index:
    preprocessor_builder.add_fn(
        fn=lambda x: x - 1,
        feature_name=output_label_index_feature_name,
        fn_name='{}_zero_based'.format(output_label_index_feature_name))

  # Replace label index by one hot representation.
  if one_hot_label:
    preprocessor_builder.add_fn(
        fn=lambda x: tf.one_hot(x, num_classes),
        feature_name=output_label_index_feature_name,
        fn_name='{}_one_hot'.format(output_label_index_feature_name))

  if add_label_name:
    parser_builder.parse_feature(
        feature_name=input_label_name_feature_name,
        feature_type=tf.io.VarLenFeature(dtype=tf.string),
        output_name=output_label_name_feature_name,
        is_context=True)
    sampler_builder.add_fn(
        fn=tf.sparse.to_dense,
        feature_name=output_label_name_feature_name,
        fn_name='{}_sparse_to_dense'.format(output_label_name_feature_name))

    # Crop or pad labels to max_num_instance.
    crop_or_pad_features_fn = functools.partial(
        processors.crop_or_pad_features,
        max_num_features=num_instances_per_frame,
        feature_dimension=1,
        constant_values='')
    preprocessor_builder.add_fn(
        fn=crop_or_pad_features_fn,
        feature_name=output_label_name_feature_name,
        fn_name='{}_crop_or_pad'.format(output_label_name_feature_name))

    if num_frames > 1:
      preprocessor_builder.add_fn(
          fn=lambda x: tf.tile(x, [num_frames, 1]),
          feature_name=output_label_name_feature_name,
          fn_name='{}_duplicate'.format(output_label_name_feature_name))

    # Reshape the feature vector in [T, N].
    target_shape = [num_frames, num_instances_per_frame]
    preprocessor_builder.add_fn(
        fn=lambda x: tf.reshape(x, target_shape),
        feature_name=output_label_name_feature_name,
        fn_name='{}_reshape'.format(output_label_name_feature_name))