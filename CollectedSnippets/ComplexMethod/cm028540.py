def __init__(self,
               block_fn,
               num_blocks: List[int],
               num_frames: int,
               model_structure: List[Any],
               input_specs: layers.InputSpec = layers.InputSpec(
                   shape=[None, None, None, None, 3]),
               model_edge_weights: Optional[List[Any]] = None,
               use_object_input: bool = False,
               attention_mode: str = 'peer',
               bn_decay: float = rf.BATCH_NORM_DECAY,
               bn_epsilon: float = rf.BATCH_NORM_EPSILON,
               use_sync_bn: bool = False,
               **kwargs):
    """Generator for AssembleNet++ models.

    Args:
      block_fn: `function` for the block to use within the model. Currently only
        has `bottleneck_block_interleave as its option`.
      num_blocks: list of 4 `int`s denoting the number of blocks to include in
        each of the 4 block groups. Each group consists of blocks that take
        inputs of the same resolution.
      num_frames: the number of frames in the input tensor.
      model_structure: AssembleNetPlus model structure in the string format.
      input_specs: `tf_keras.layers.InputSpec` specs of the input tensor.
        Dimension should be `[batch*time, height, width, channels]`.
      model_edge_weights: AssembleNet model structure connection weight in the
        string format.
      use_object_input : 'bool' values whether using object inputs
      attention_mode : 'str' , default = 'self', If we use peer attention 'peer'
      bn_decay: `float` batch norm decay parameter to use.
      bn_epsilon: `float` batch norm epsilon parameter to use.
      use_sync_bn: use synchronized batch norm for TPU.
      **kwargs: pass through arguments.

    Returns:
      Model `function` that takes in `inputs` and `is_training` and returns the
      output `Tensor` of the AssembleNetPlus model.
    """
    data_format = tf_keras.backend.image_data_format()

    # Creation of the model graph.
    logging.info('model_structure=%r', model_structure)
    logging.info('model_structure=%r', model_structure)
    logging.info('model_edge_weights=%r', model_edge_weights)
    structure = model_structure

    if use_object_input:
      original_inputs = tf_keras.Input(shape=input_specs[0].shape[1:])
      object_inputs = tf_keras.Input(shape=input_specs[1].shape[1:])
      input_specs = input_specs[0]
    else:
      original_inputs = tf_keras.Input(shape=input_specs.shape[1:])
      object_inputs = None

    original_num_frames = num_frames
    assert num_frames > 0, f'Invalid num_frames {num_frames}'

    grouping = {-3: [], -2: [], -1: [], 0: [], 1: [], 2: [], 3: []}
    for i in range(len(structure)):
      grouping[structure[i][0]].append(i)

    stem_count = len(grouping[-3]) + len(grouping[-2]) + len(grouping[-1])

    assert stem_count != 0
    stem_filters = 128 // stem_count

    if len(input_specs.shape) == 5:
      first_dim = (
          input_specs.shape[0] * input_specs.shape[1]
          if input_specs.shape[0] and input_specs.shape[1] else -1)
      reshape_inputs = tf.reshape(original_inputs,
                                  (first_dim,) + input_specs.shape[2:])
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
          inputs = asn.rgb_conv_stem(
              reshape_inputs,
              original_num_frames,
              stem_filters,
              temporal_dilation=structure[i][1],
              bn_decay=bn_decay,
              bn_epsilon=bn_epsilon,
              use_sync_bn=use_sync_bn)
          streams.append(inputs)
        elif structure[i][0] == -2:
          inputs = asn.flow_conv_stem(
              flow_inputs,
              stem_filters,
              temporal_dilation=structure[i][1],
              bn_decay=bn_decay,
              bn_epsilon=bn_epsilon,
              use_sync_bn=use_sync_bn)
          streams.append(inputs)
        elif structure[i][0] == -3:
          # In order to use the object inputs, you need to feed your object
          # input tensor here.
          inputs = object_conv_stem(object_inputs)
          streams.append(inputs)
        else:
          block_number = structure[i][0]
          combined_inputs = [
              streams[structure[i][1][j]]
              for j in range(0, len(structure[i][1]))
          ]

          logging.info(grouping)
          nodes_below = []
          for k in range(-3, structure[i][0]):
            nodes_below = nodes_below + grouping[k]

          peers = []
          if attention_mode:
            lg_channel = -1
            # To show structures for attention we show nodes_below
            logging.info(nodes_below)
            for k in nodes_below:
              logging.info(streams[k].shape)
              lg_channel = max(streams[k].shape[3], lg_channel)

            for node_index in nodes_below:
              attn = tf.reduce_mean(streams[node_index], [1, 2])

              attn = tf_keras.layers.Dense(
                  units=lg_channel,
                  kernel_initializer=tf.random_normal_initializer(stddev=.01))(
                      inputs=attn)
              peers.append(attn)

          combined_inputs = fusion_with_peer_attention(
              combined_inputs,
              index=i,
              attention_mode=attention_mode,
              attention_in=peers,
              use_5d_mode=False)

          graph = asn.block_group(
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

    if use_object_input:
      inputs = [original_inputs, object_inputs]
    else:
      inputs = original_inputs

    super(AssembleNetPlus, self).__init__(
        inputs=inputs, outputs=streams, **kwargs)