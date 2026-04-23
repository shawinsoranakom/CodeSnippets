def build(input_reader_config):
  """Builds a tensor dictionary based on the InputReader config.

  Args:
    input_reader_config: A input_reader_pb2.InputReader object.

  Returns:
    A tensor dict based on the input_reader_config.

  Raises:
    ValueError: On invalid input reader proto.
    ValueError: If no input paths are specified.
  """
  if not isinstance(input_reader_config, input_reader_pb2.InputReader):
    raise ValueError('input_reader_config not of type '
                     'input_reader_pb2.InputReader.')

  if input_reader_config.WhichOneof('input_reader') == 'tf_record_input_reader':
    config = input_reader_config.tf_record_input_reader
    if not config.input_path:
      raise ValueError('At least one input path must be specified in '
                       '`input_reader_config`.')
    _, string_tensor = parallel_reader.parallel_read(
        config.input_path[:],  # Convert `RepeatedScalarContainer` to list.
        reader_class=tf.TFRecordReader,
        num_epochs=(input_reader_config.num_epochs
                    if input_reader_config.num_epochs else None),
        num_readers=input_reader_config.num_readers,
        shuffle=input_reader_config.shuffle,
        dtypes=[tf.string, tf.string],
        capacity=input_reader_config.queue_capacity,
        min_after_dequeue=input_reader_config.min_after_dequeue)

    label_map_proto_file = None
    if input_reader_config.HasField('label_map_path'):
      label_map_proto_file = input_reader_config.label_map_path
    input_type = input_reader_config.input_type
    if input_type == input_reader_pb2.InputType.Value('TF_EXAMPLE'):
      decoder = tf_example_decoder.TfExampleDecoder(
          load_instance_masks=input_reader_config.load_instance_masks,
          instance_mask_type=input_reader_config.mask_type,
          label_map_proto_file=label_map_proto_file,
          load_context_features=input_reader_config.load_context_features)
      return decoder.decode(string_tensor)
    elif input_type == input_reader_pb2.InputType.Value('TF_SEQUENCE_EXAMPLE'):
      decoder = tf_sequence_example_decoder.TfSequenceExampleDecoder(
          label_map_proto_file=label_map_proto_file,
          load_context_features=input_reader_config.load_context_features,
          load_context_image_ids=input_reader_config.load_context_image_ids)
      return decoder.decode(string_tensor)
    raise ValueError('Unsupported input_type.')
  raise ValueError('Unsupported input_reader_config.')