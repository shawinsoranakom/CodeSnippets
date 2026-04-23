def _compute_buffered_causal_padding(self,
                                       inputs: tf.Tensor,
                                       use_buffered_input: bool = False,
                                       time_axis: int = 1,
                                       ) -> List[List[int]]:
    """Calculates padding for 'causal' option for conv layers.

    Args:
      inputs: An optional input `tf.Tensor` to be padded.
      use_buffered_input: A `bool`. If True, use 'valid' padding along the time
        dimension. This should be set when applying the stream buffer.
      time_axis: An `int` of the axis of the time dimension.

    Returns:
      A list of paddings for `tf.pad`.
    """
    input_shape = tf.shape(inputs)[1:-1]

    if tf_keras.backend.image_data_format() == 'channels_first':
      raise ValueError('"channels_first" mode is unsupported.')

    kernel_size_effective = [
        (self.kernel_size[i] +
         (self.kernel_size[i] - 1) * (self.dilation_rate[i] - 1))
        for i in range(self.rank)
    ]
    pad_total = [kernel_size_effective[0] - 1]
    for i in range(1, self.rank):
      overlap = (input_shape[i] - 1) % self.strides[i] + 1
      pad_total.append(tf.maximum(kernel_size_effective[i] - overlap, 0))
    pad_beg = [pad_total[i] // 2 for i in range(self.rank)]
    pad_end = [pad_total[i] - pad_beg[i] for i in range(self.rank)]
    padding = [[pad_beg[i], pad_end[i]] for i in range(self.rank)]
    padding = [[0, 0]] + padding + [[0, 0]]

    if use_buffered_input:
      padding[time_axis] = [0, 0]
    else:
      padding[time_axis] = [padding[time_axis][0] + padding[time_axis][1], 0]
    return padding