def __init__(self,
               input_specs: Dict[str, tf.TensorShape],
               task_outputs: Mapping[str, int],
               input_levels: List[str],
               heatmap_bias: float = -2.19,
               **kwargs):
    """CenterNet Head Initialization.

    Args:
      input_specs: A `dict` of input specifications.
      task_outputs: A `dict`, with key-value pairs denoting the names of the
        outputs and the desired channel depth of each output.
      input_levels: list of str representing the level used as input to the
        CenternetHead from the backbone. For example, ['2_0', '2'] should be
        set for hourglass-104 has two hourglass-52 modules, since the output
        of hourglass backbones is organized as:
          '2' -> the last layer of output
          '2_0' -> the first layer of output
          ......
          '2_{num_hourglasses-2}' -> the second to last layer of output.
      heatmap_bias: `float`, constant value to initialize the convolution layer
        bias vector if it is responsible for generating a heatmap (not for
        regressed predictions).
      **kwargs: Additional keyword arguments to be passed.

    Returns:
      dictionary where the keys-value pairs denote the names of the output
      and the respective output tensor
    """
    assert input_levels, f'Please specify input levels: {input_levels}'

    self._input_specs = input_specs
    self._task_outputs = task_outputs
    self._input_levels = input_levels
    self._heatmap_bias = heatmap_bias
    self._num_inputs = len(input_levels)

    inputs = {level: tf_keras.layers.Input(shape=self._input_specs[level][1:])
              for level in input_levels}
    outputs = {}

    for key in self._task_outputs:
      # pylint: disable=g-complex-comprehension
      outputs[key] = [
          cn_nn_blocks.CenterNetHeadConv(
              output_filters=self._task_outputs[key],
              bias_init=self._heatmap_bias if 'heatmaps' in key else 0,
              name=key + str(i),
          )(inputs[i])
          for i in input_levels
      ]

    self._output_specs = {
        key: [value[i].get_shape() for i in range(self._num_inputs)]
        for key, value in outputs.items()
    }

    super().__init__(inputs=inputs, outputs=outputs,
                     name='CenterNetHead', **kwargs)