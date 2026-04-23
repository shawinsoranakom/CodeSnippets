def expanded_conv(input_tensor,
                  num_outputs,
                  expansion_size=expand_input_by_factor(6),
                  stride=1,
                  rate=1,
                  kernel_size=(3, 3),
                  residual=True,
                  normalizer_fn=None,
                  split_projection=1,
                  split_expansion=1,
                  split_divisible_by=8,
                  expansion_transform=None,
                  depthwise_location='expansion',
                  depthwise_channel_multiplier=1,
                  endpoints=None,
                  use_explicit_padding=False,
                  padding='SAME',
                  inner_activation_fn=None,
                  depthwise_activation_fn=None,
                  project_activation_fn=tf.identity,
                  depthwise_fn=slim.separable_conv2d,
                  expansion_fn=split_conv,
                  projection_fn=split_conv,
                  scope=None):
  """Depthwise Convolution Block with expansion.

  Builds a composite convolution that has the following structure
  expansion (1x1) -> depthwise (kernel_size) -> projection (1x1)

  Args:
    input_tensor: input
    num_outputs: number of outputs in the final layer.
    expansion_size: the size of expansion, could be a constant or a callable.
      If latter it will be provided 'num_inputs' as an input. For forward
      compatibility it should accept arbitrary keyword arguments.
      Default will expand the input by factor of 6.
    stride: depthwise stride
    rate: depthwise rate
    kernel_size: depthwise kernel
    residual: whether to include residual connection between input
      and output.
    normalizer_fn: batchnorm or otherwise
    split_projection: how many ways to split projection operator
      (that is conv expansion->bottleneck)
    split_expansion: how many ways to split expansion op
      (that is conv bottleneck->expansion) ops will keep depth divisible
      by this value.
    split_divisible_by: make sure every split group is divisible by this number.
    expansion_transform: Optional function that takes expansion
      as a single input and returns output.
    depthwise_location: where to put depthwise covnvolutions supported
      values None, 'input', 'output', 'expansion'
    depthwise_channel_multiplier: depthwise channel multiplier:
    each input will replicated (with different filters)
    that many times. So if input had c channels,
    output will have c x depthwise_channel_multpilier.
    endpoints: An optional dictionary into which intermediate endpoints are
      placed. The keys "expansion_output", "depthwise_output",
      "projection_output" and "expansion_transform" are always populated, even
      if the corresponding functions are not invoked.
    use_explicit_padding: Use 'VALID' padding for convolutions, but prepad
      inputs so that the output dimensions are the same as if 'SAME' padding
      were used.
    padding: Padding type to use if `use_explicit_padding` is not set.
    inner_activation_fn: activation function to use in all inner convolutions.
    If none, will rely on slim default scopes.
    depthwise_activation_fn: activation function to use for deptwhise only.
      If not provided will rely on slim default scopes. If both
      inner_activation_fn and depthwise_activation_fn are provided,
      depthwise_activation_fn takes precedence over inner_activation_fn.
    project_activation_fn: activation function for the project layer.
    (note this layer is not affected by inner_activation_fn)
    depthwise_fn: Depthwise convolution function.
    expansion_fn: Expansion convolution function. If use custom function then
      "split_expansion" and "split_divisible_by" will be ignored.
    projection_fn: Projection convolution function. If use custom function then
      "split_projection" and "split_divisible_by" will be ignored.

    scope: optional scope.

  Returns:
    Tensor of depth num_outputs

  Raises:
    TypeError: on inval
  """
  conv_defaults = {}
  dw_defaults = {}
  if inner_activation_fn is not None:
    conv_defaults['activation_fn'] = inner_activation_fn
    dw_defaults['activation_fn'] = inner_activation_fn
  if depthwise_activation_fn is not None:
    dw_defaults['activation_fn'] = depthwise_activation_fn
  # pylint: disable=g-backslash-continuation
  with tf.variable_scope(scope, default_name='expanded_conv') as s, \
       tf.name_scope(s.original_name_scope), \
      slim.arg_scope((slim.conv2d,), **conv_defaults), \
       slim.arg_scope((slim.separable_conv2d,), **dw_defaults):
    prev_depth = input_tensor.get_shape().as_list()[3]
    if  depthwise_location not in [None, 'input', 'output', 'expansion']:
      raise TypeError('%r is unknown value for depthwise_location' %
                      depthwise_location)
    if use_explicit_padding:
      if padding != 'SAME':
        raise TypeError('`use_explicit_padding` should only be used with '
                        '"SAME" padding.')
      padding = 'VALID'
    depthwise_func = functools.partial(
        depthwise_fn,
        num_outputs=None,
        kernel_size=kernel_size,
        depth_multiplier=depthwise_channel_multiplier,
        stride=stride,
        rate=rate,
        normalizer_fn=normalizer_fn,
        padding=padding,
        scope='depthwise')
    # b1 -> b2 * r -> b2
    #   i -> (o * r) (bottleneck) -> o
    input_tensor = tf.identity(input_tensor, 'input')
    net = input_tensor

    if depthwise_location == 'input':
      if use_explicit_padding:
        net = _fixed_padding(net, kernel_size, rate)
      net = depthwise_func(net, activation_fn=None)
      net = tf.identity(net, name='depthwise_output')
      if endpoints is not None:
        endpoints['depthwise_output'] = net

    if callable(expansion_size):
      inner_size = expansion_size(num_inputs=prev_depth)
    else:
      inner_size = expansion_size

    if inner_size > net.shape[3]:
      if expansion_fn == split_conv:
        expansion_fn = functools.partial(
            expansion_fn,
            num_ways=split_expansion,
            divisible_by=split_divisible_by,
            stride=1)
      net = expansion_fn(
          net,
          inner_size,
          scope='expand',
          normalizer_fn=normalizer_fn)
      net = tf.identity(net, 'expansion_output')
      if endpoints is not None:
        endpoints['expansion_output'] = net

    if depthwise_location == 'expansion':
      if use_explicit_padding:
        net = _fixed_padding(net, kernel_size, rate)
      net = depthwise_func(net)
      net = tf.identity(net, name='depthwise_output')
      if endpoints is not None:
        endpoints['depthwise_output'] = net

    if expansion_transform:
      net = expansion_transform(expansion_tensor=net, input_tensor=input_tensor)
    # Note in contrast with expansion, we always have
    # projection to produce the desired output size.
    if projection_fn == split_conv:
      projection_fn = functools.partial(
          projection_fn,
          num_ways=split_projection,
          divisible_by=split_divisible_by,
          stride=1)
    net = projection_fn(
        net,
        num_outputs,
        scope='project',
        normalizer_fn=normalizer_fn,
        activation_fn=project_activation_fn)
    if endpoints is not None:
      endpoints['projection_output'] = net
    if depthwise_location == 'output':
      if use_explicit_padding:
        net = _fixed_padding(net, kernel_size, rate)
      net = depthwise_func(net, activation_fn=None)
      net = tf.identity(net, name='depthwise_output')
      if endpoints is not None:
        endpoints['depthwise_output'] = net

    if callable(residual):  # custom residual
      net = residual(input_tensor=input_tensor, output_tensor=net)
    elif (residual and
          # stride check enforces that we don't add residuals when spatial
          # dimensions are None
          stride == 1 and
          # Depth matches
          net.get_shape().as_list()[3] ==
          input_tensor.get_shape().as_list()[3]):
      net += input_tensor
    return tf.identity(net, name='output')