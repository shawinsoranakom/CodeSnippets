def multi_connection_fusion(inputs: List[tf.Tensor],
                            index: Optional[int] = None,
                            use_5d_mode: bool = False,
                            model_edge_weights: Optional[List[Any]] = None):
  """Do weighted summation of multiple different sized tensors.

  A weight is assigned for each connection (i.e., each input tensor), and their
  summation weights are learned. Uses spatial max pooling and 1x1 conv.
  to match their sizes.

  Args:
    inputs: A `Tensor`. Either 4D or 5D, depending of use_5d_mode.
    index: `int` index of the block within the AssembleNet architecture. Used
      for summation weight initial loading.
    use_5d_mode: `bool` indicating whether the inputs are in 5D tensor or 4D.
    model_edge_weights: AssembleNet model structure connection weights in the
      string format.

  Returns:
    The output `Tensor` after concatenation.
  """

  if use_5d_mode:
    h_channel_loc = 2
    conv_function = conv3d_same_padding
  else:
    h_channel_loc = 1
    conv_function = conv2d_fixed_padding

  # If only 1 input.
  if len(inputs) == 1:
    return inputs[0]

  # get smallest spatial size and largest channels
  sm_size = [10000, 10000]
  lg_channel = 0
  for inp in inputs:
    # assume batch X height x width x channels
    sm_size[0] = min(sm_size[0], inp.shape[h_channel_loc])
    sm_size[1] = min(sm_size[1], inp.shape[h_channel_loc + 1])
    lg_channel = max(lg_channel, inp.shape[-1])

  per_channel_inps = _ApplyEdgeWeight(
      weights_shape=[len(inputs)],
      index=index,
      use_5d_mode=use_5d_mode,
      model_edge_weights=model_edge_weights)(
          inputs)

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
            tf.add_n(channel_inps), lg_channel, kernel_size=1, strides=1)
      inps.append(inp)

  return tf.add_n(inps)