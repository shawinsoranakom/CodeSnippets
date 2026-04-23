def conv2d(inputs,
           num_outputs,
           kernel_size,
           stride=1,
           padding='SAME',
           data_format=None,
           rate=1,
           activation_fn=tf.nn.relu,
           normalizer_fn=None,
           normalizer_params=None,
           weights_initializer=contrib_layers.xavier_initializer(),
           weights_regularizer=None,
           biases_initializer=tf.zeros_initializer(),
           biases_regularizer=None,
           use_weight_standardization=False,
           reuse=None,
           variables_collections=None,
           outputs_collections=None,
           trainable=True,
           scope=None):
  """Adds a 2D convolution followed by an optional batch_norm layer.

  `convolution` creates a variable called `weights`, representing the
  convolutional kernel, that is convolved (actually cross-correlated) with the
  `inputs` to produce a `Tensor` of activations. If a `normalizer_fn` is
  provided (such as `batch_norm`), it is then applied. Otherwise, if
  `normalizer_fn` is None and a `biases_initializer` is provided then a `biases`
  variable would be created and added the activations. Finally, if
  `activation_fn` is not `None`, it is applied to the activations as well.

  Performs atrous convolution with input stride/dilation rate equal to `rate`
  if a value > 1 for any dimension of `rate` is specified.  In this case
  `stride` values != 1 are not supported.

  Args:
    inputs: A Tensor of rank N+2 of shape `[batch_size] + input_spatial_shape +
      [in_channels]` if data_format does not start with "NC" (default), or
      `[batch_size, in_channels] + input_spatial_shape` if data_format starts
      with "NC".
    num_outputs: Integer, the number of output filters.
    kernel_size: A sequence of N positive integers specifying the spatial
      dimensions of the filters.  Can be a single integer to specify the same
      value for all spatial dimensions.
    stride: A sequence of N positive integers specifying the stride at which to
      compute output.  Can be a single integer to specify the same value for all
      spatial dimensions.  Specifying any `stride` value != 1 is incompatible
      with specifying any `rate` value != 1.
    padding: One of `"VALID"` or `"SAME"`.
    data_format: A string or None.  Specifies whether the channel dimension of
      the `input` and output is the last dimension (default, or if `data_format`
      does not start with "NC"), or the second dimension (if `data_format`
      starts with "NC").  For N=1, the valid values are "NWC" (default) and
      "NCW".  For N=2, the valid values are "NHWC" (default) and "NCHW". For
      N=3, the valid values are "NDHWC" (default) and "NCDHW".
    rate: A sequence of N positive integers specifying the dilation rate to use
      for atrous convolution.  Can be a single integer to specify the same value
      for all spatial dimensions.  Specifying any `rate` value != 1 is
      incompatible with specifying any `stride` value != 1.
    activation_fn: Activation function. The default value is a ReLU function.
      Explicitly set it to None to skip it and maintain a linear activation.
    normalizer_fn: Normalization function to use instead of `biases`. If
      `normalizer_fn` is provided then `biases_initializer` and
      `biases_regularizer` are ignored and `biases` are not created nor added.
      default set to None for no normalizer function
    normalizer_params: Normalization function parameters.
    weights_initializer: An initializer for the weights.
    weights_regularizer: Optional regularizer for the weights.
    biases_initializer: An initializer for the biases. If None skip biases.
    biases_regularizer: Optional regularizer for the biases.
    use_weight_standardization: Boolean, whether the layer uses weight
      standardization.
    reuse: Whether or not the layer and its variables should be reused. To be
      able to reuse the layer scope must be given.
    variables_collections: Optional list of collections for all the variables or
      a dictionary containing a different list of collection per variable.
    outputs_collections: Collection to add the outputs.
    trainable: If `True` also add variables to the graph collection
      `GraphKeys.TRAINABLE_VARIABLES` (see tf.Variable).
    scope: Optional scope for `variable_scope`.

  Returns:
    A tensor representing the output of the operation.

  Raises:
    ValueError: If `data_format` is invalid.
    ValueError: Both 'rate' and `stride` are not uniformly 1.
  """
  if data_format not in [None, 'NWC', 'NCW', 'NHWC', 'NCHW', 'NDHWC', 'NCDHW']:
    raise ValueError('Invalid data_format: %r' % (data_format,))

  # pylint: disable=protected-access
  layer_variable_getter = layers._build_variable_getter({
      'bias': 'biases',
      'kernel': 'weights'
  })
  # pylint: enable=protected-access
  with tf.variable_scope(
      scope, 'Conv', [inputs], reuse=reuse,
      custom_getter=layer_variable_getter) as sc:
    inputs = tf.convert_to_tensor(inputs)
    input_rank = inputs.get_shape().ndims

    if input_rank != 4:
      raise ValueError('Convolution expects input with rank %d, got %d' %
                       (4, input_rank))

    data_format = ('channels_first' if data_format and
                   data_format.startswith('NC') else 'channels_last')
    layer = Conv2D(
        filters=num_outputs,
        kernel_size=kernel_size,
        strides=stride,
        padding=padding,
        data_format=data_format,
        dilation_rate=rate,
        activation=None,
        use_bias=not normalizer_fn and biases_initializer,
        kernel_initializer=weights_initializer,
        bias_initializer=biases_initializer,
        kernel_regularizer=weights_regularizer,
        bias_regularizer=biases_regularizer,
        use_weight_standardization=use_weight_standardization,
        activity_regularizer=None,
        trainable=trainable,
        name=sc.name,
        dtype=inputs.dtype.base_dtype,
        _scope=sc,
        _reuse=reuse)
    outputs = layer.apply(inputs)

    # Add variables to collections.
    # pylint: disable=protected-access
    layers._add_variable_to_collections(layer.kernel, variables_collections,
                                        'weights')
    if layer.use_bias:
      layers._add_variable_to_collections(layer.bias, variables_collections,
                                          'biases')
    # pylint: enable=protected-access
    if normalizer_fn is not None:
      normalizer_params = normalizer_params or {}
      outputs = normalizer_fn(outputs, **normalizer_params)

    if activation_fn is not None:
      outputs = activation_fn(outputs)
    return utils.collect_named_outputs(outputs_collections, sc.name, outputs)