def __init__(
      self,
      block_fn,
      num_blocks: List[int],
      num_frames: int,
      model_structure: List[Any],
      input_specs: layers.InputSpec = layers.InputSpec(
          shape=[None, None, None, None, 3]),
      model_edge_weights: Optional[List[Any]] = None,
      bn_decay: float = rf.BATCH_NORM_DECAY,
      bn_epsilon: float = rf.BATCH_NORM_EPSILON,
      use_sync_bn: bool = False,
      combine_method: str = 'sigmoid',
      **kwargs):
    """Generator for AssembleNet v1 models.

    Args:
      block_fn: `function` for the block to use within the model. Currently only
        has `bottleneck_block_interleave as its option`.
      num_blocks: list of 4 `int`s denoting the number of blocks to include in
        each of the 4 block groups. Each group consists of blocks that take
        inputs of the same resolution.
      num_frames: the number of frames in the input tensor.
      model_structure: AssembleNet model structure in the string format.
      input_specs: `tf_keras.layers.InputSpec` specs of the input tensor.
        Dimension should be `[batch*time, height, width, channels]`.
      model_edge_weights: AssembleNet model structure connection weights in the
        string format.
      bn_decay: `float` batch norm decay parameter to use.
      bn_epsilon: `float` batch norm epsilon parameter to use.
      use_sync_bn: use synchronized batch norm for TPU.
      combine_method: 'str' for the weighted summation to fuse different blocks.
      **kwargs: pass through arguments.
    """
    inputs = tf_keras.Input(shape=input_specs.shape[1:])
    data_format = tf_keras.backend.image_data_format()

    # Creation of the model graph.
    logging.info('model_structure=%r', model_structure)
    logging.info('model_structure=%r', model_structure)
    logging.info('model_edge_weights=%r', model_edge_weights)
    structure = model_structure

    original_num_frames = num_frames
    assert num_frames > 0, f'Invalid num_frames {num_frames}'

    grouping = {-3: [], -2: [], -1: [], 0: [], 1: [], 2: [], 3: []}
    for i in range(len(structure)):
      grouping[structure[i][0]].append(i)

    stem_count = len(grouping[-3]) + len(grouping[-2]) + len(grouping[-1])

    assert stem_count != 0
    stem_filters = 128 // stem_count

    original_inputs = inputs
    if len(input_specs.shape) == 5:
      first_dim = (
          input_specs.shape[0] * input_specs.shape[1]
          if input_specs.shape[0] and input_specs.shape[1] else -1)
      reshape_inputs = tf.reshape(inputs, (first_dim,) + input_specs.shape[2:])
    elif len(input_specs.shape) == 4:
      reshape_inputs = original_inputs
    else:
      raise ValueError(
          f'Expect input spec to be 4 or 5 dimensions {input_specs.shape}')
    if grouping[-2]:
      # Instead of loading optical flows as inputs from data pipeline, we are
      # applying the "Representation Flow" to RGB frames so that we can compute
      # the flow within TPU/GPU on fly. It's essentially optical flow since we
      # do it with RGBs.
      axis = 3 if data_format == 'channels_last' else 1
      flow_inputs = rf.RepresentationFlow(
          original_num_frames,
          depth=reshape_inputs.shape.as_list()[axis],
          num_iter=40,
          bottleneck=1)(
              reshape_inputs)
    streams = []

    for i in range(len(structure)):
      with tf.name_scope('Node_' + str(i)):
        if structure[i][0] == -1:
          inputs = rgb_conv_stem(
              reshape_inputs,
              original_num_frames,
              stem_filters,
              temporal_dilation=structure[i][1],
              bn_decay=bn_decay,
              bn_epsilon=bn_epsilon,
              use_sync_bn=use_sync_bn)
          streams.append(inputs)
        elif structure[i][0] == -2:
          inputs = flow_conv_stem(
              flow_inputs,
              stem_filters,
              temporal_dilation=structure[i][1],
              bn_decay=bn_decay,
              bn_epsilon=bn_epsilon,
              use_sync_bn=use_sync_bn)
          streams.append(inputs)

        else:
          num_frames = original_num_frames
          block_number = structure[i][0]

          combined_inputs = []
          if combine_method == 'concat':
            combined_inputs = [
                streams[structure[i][1][j]]
                for j in range(0, len(structure[i][1]))
            ]

            combined_inputs = spatial_resize_and_concat(combined_inputs)

          else:
            combined_inputs = [
                streams[structure[i][1][j]]
                for j in range(0, len(structure[i][1]))
            ]

            combined_inputs = multi_connection_fusion(
                combined_inputs, index=i, model_edge_weights=model_edge_weights)

          graph = block_group(
              inputs=combined_inputs,
              filters=structure[i][2],
              block_fn=block_fn,
              blocks=num_blocks[block_number],
              strides=structure[i][4],
              name='block_group' + str(i),
              block_level=structure[i][0],
              num_frames=num_frames,
              temporal_dilation=structure[i][3])

          streams.append(graph)

    super(AssembleNet, self).__init__(
        inputs=original_inputs, outputs=streams, **kwargs)