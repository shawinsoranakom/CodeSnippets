def __init__(
      self,
      model_id='yolov7',
      input_specs=tf_keras.layers.InputSpec(shape=[None, None, None, 3]),
      use_sync_bn=False,
      norm_momentum=0.99,
      norm_epsilon=0.001,
      activation='swish',
      kernel_initializer='VarianceScaling',
      kernel_regularizer=None,
      bias_initializer='zeros',
      bias_regularizer=None,
      **kwargs):
    """Initializes the YOLOv7 backbone.

    Args:
      model_id: a `str` represents the model variants.
      input_specs: a `tf_keras.layers.InputSpec` of the input tensor.
      use_sync_bn: if set to `True`, use synchronized batch normalization.
      norm_momentum: a `float` of normalization momentum for the moving average.
      norm_epsilon: a small `float` added to variance to avoid dividing by zero.
      activation: a `str` name of the activation function.
      kernel_initializer: a `str` for kernel initializer of convolutional
        layers.
      kernel_regularizer: a `tf_keras.regularizers.Regularizer` object for
        Conv2D. Default to None.
      bias_initializer: a `str` for bias initializer of convolutional layers.
      bias_regularizer: a `tf_keras.regularizers.Regularizer` object for Conv2D.
        Default to None.
      **kwargs: Additional keyword arguments to be passed.
    """

    self._model_id = model_id
    self._input_specs = input_specs
    self._use_sync_bn = use_sync_bn
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon
    self._activation = activation

    self._kernel_initializer = initializer_ops.pytorch_kernel_initializer(
        kernel_initializer
    )
    self._kernel_regularizer = kernel_regularizer
    self._bias_initializer = bias_initializer
    self._bias_regularizer = bias_regularizer

    inputs = tf_keras.layers.Input(shape=input_specs.shape[1:])

    block_specs = BACKBONES[model_id.lower()]
    outputs = []
    endpoints = {}
    level = 3
    for spec in block_specs:
      block_kwargs = dict(zip(_BLOCK_SPEC_SCHEMAS[spec[0]], spec))

      block_fn_str = block_kwargs.pop('block_fn')
      from_index = block_kwargs.pop('from')
      is_output = block_kwargs.pop('is_output')

      if not outputs:
        x = inputs
      elif isinstance(from_index, int):
        x = outputs[from_index]
      else:
        x = [outputs[idx] for idx in from_index]

      if block_fn_str in ['convbn']:
        block_kwargs.update({
            'use_sync_bn': self._use_sync_bn,
            'norm_momentum': self._norm_momentum,
            'norm_epsilon': self._norm_epsilon,
            'activation': self._activation,
            'kernel_initializer': self._kernel_initializer,
            'kernel_regularizer': self._kernel_regularizer,
            'bias_initializer': self._bias_initializer,
            'bias_regularizer': self._bias_regularizer,
        })
      block_fn = _BLOCK_FNS[block_fn_str](**block_kwargs)

      x = block_fn(x)
      outputs.append(x)
      if is_output:
        endpoints[str(level)] = x
        level += 1
    self._output_specs = {k: v.get_shape() for k, v in endpoints.items()}
    super().__init__(inputs=inputs, outputs=endpoints, **kwargs)