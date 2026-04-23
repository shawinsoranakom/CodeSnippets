def call(self,
           inputs: List[tf.Tensor],
           training: Optional[bool] = None) -> Mapping[Any, List[tf.Tensor]]:
    use_5d_mode = self._use_5d_mode
    dtype = inputs[0].dtype
    assert len(inputs) > 1

    if use_5d_mode:
      h_channel_loc = 2
    else:
      h_channel_loc = 1

    # get smallest spatial size and largest channels
    sm_size = [10000, 10000]
    lg_channel = 0
    for inp in inputs:
      # assume batch X height x width x channels
      sm_size[0] = min(sm_size[0], inp.shape[h_channel_loc])
      sm_size[1] = min(sm_size[1], inp.shape[h_channel_loc + 1])
      # Note that, when using object inputs, object channel sizes are usually
      # big. Since we do not want the object channel size to increase the number
      # of parameters for every fusion, we exclude it when computing lg_channel.
      if inp.shape[-1] > lg_channel and inp.shape[-1] != self._num_object_classes:  # pylint: disable=line-too-long
        lg_channel = inp.shape[3]

    # loads or creates weight variables to fuse multiple inputs
    weights = tf.math.sigmoid(tf.cast(self._edge_weights, dtype))

    # Compute weighted inputs. We group inputs with the same channels.
    per_channel_inps = dict({0: []})
    for i, inp in enumerate(inputs):
      if inp.shape[h_channel_loc] != sm_size[0] or inp.shape[h_channel_loc + 1] != sm_size[1]:  # pylint: disable=line-too-long
        assert sm_size[0] != 0
        ratio = (inp.shape[h_channel_loc] + 1) // sm_size[0]
        if use_5d_mode:
          inp = tf_keras.layers.MaxPool3D([1, ratio, ratio], [1, ratio, ratio],
                                          padding='same')(
                                              inp)
        else:
          inp = tf_keras.layers.MaxPool2D([ratio, ratio], ratio,
                                          padding='same')(
                                              inp)

      weights = tf.cast(weights, inp.dtype)
      if inp.shape[-1] in per_channel_inps:
        per_channel_inps[inp.shape[-1]].append(weights[i] * inp)
      else:
        per_channel_inps.update({inp.shape[-1]: [weights[i] * inp]})

    return per_channel_inps