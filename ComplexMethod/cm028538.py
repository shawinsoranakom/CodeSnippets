def fusion_with_peer_attention(inputs: List[tf.Tensor],
                               index: Optional[int] = None,
                               attention_mode: Optional[str] = None,
                               attention_in: Optional[List[tf.Tensor]] = None,
                               use_5d_mode: bool = False,
                               model_edge_weights: Optional[List[Any]] = None,
                               num_object_classes: Optional[int] = None):
  """Weighted summation of multiple tensors, while using peer-attention.

  Summation weights are to be learned. Uses spatial max pooling and 1x1 conv.
  to match their sizes. Before the summation, each connection (i.e., each input)
  itself is scaled with channel-wise peer-attention. Notice that attention is
  applied for each connection, conditioned based on attention_in.

  Args:
    inputs: A list of `Tensors`. Either 4D or 5D, depending of use_5d_mode.
    index: `int` index of the block within the AssembleNet architecture. Used
      for summation weight initial loading.
    attention_mode: `str` specifying mode. If not `peer', does self-attention.
    attention_in: A list of `Tensors' of size [batch*time, channels].
    use_5d_mode: `bool` indicating whether the inputs are in 5D tensor or 4D.
    model_edge_weights: AssembleNet model structure connection weights in the
      string format.
    num_object_classes: Assemblenet++ structure used object inputs so we should
      use what dataset classes you might be use (e.g. ADE-20k 151 classes)

  Returns:
    The output `Tensor` after concatenation.
  """
  if use_5d_mode:
    h_channel_loc = 2
    conv_function = asn.conv3d_same_padding
  else:
    h_channel_loc = 1
    conv_function = asn.conv2d_fixed_padding

  # If only 1 input.
  if len(inputs) == 1:
    inputs[0] = apply_attention(inputs[0], attention_mode, attention_in,
                                use_5d_mode)
    return inputs[0]

  # get smallest spatial size and largest channels
  sm_size = [10000, 10000]
  lg_channel = 0
  for inp in inputs:
    # assume batch X height x width x channels
    sm_size[0] = min(sm_size[0], inp.shape[h_channel_loc])
    sm_size[1] = min(sm_size[1], inp.shape[h_channel_loc + 1])
    # Note that, when using object inputs, object channel sizes are usually big.
    # Since we do not want the object channel size to increase the number of
    # parameters for every fusion, we exclude it when computing lg_channel.
    if inp.shape[-1] > lg_channel and inp.shape[-1] != num_object_classes:  # pylint: disable=line-too-long
      lg_channel = inp.shape[3]

  per_channel_inps = _ApplyEdgeWeight(
      weights_shape=[len(inputs)],
      index=index,
      use_5d_mode=use_5d_mode,
      model_edge_weights=model_edge_weights)(
          inputs)

  # Implementation of connectivity with peer-attention
  if attention_mode:
    for key, channel_inps in per_channel_inps.items():
      for idx in range(len(channel_inps)):
        with tf.name_scope('Connection_' + str(key) + '_' + str(idx)):
          channel_inps[idx] = apply_attention(channel_inps[idx], attention_mode,
                                              attention_in, use_5d_mode)
  # Adding 1x1 conv layers (to match channel size) and fusing all inputs.
  # We add inputs with the same channels first before applying 1x1 conv to save
  # memory.
  inps = []
  for key, channel_inps in per_channel_inps.items():
    if len(channel_inps) < 1:
      continue
    if len(channel_inps) == 1:
      if key == lg_channel:
        inp = channel_inps[0]
      else:
        inp = conv_function(
            channel_inps[0], lg_channel, kernel_size=1, strides=1)
      inps.append(inp)
    else:
      if key == lg_channel:
        inp = tf.add_n(channel_inps)
      else:
        inp = conv_function(
            channel_inps[0], lg_channel, kernel_size=1, strides=1)
      inps.append(inp)

  return tf.add_n(inps)