def mobilenet_base(  # pylint: disable=invalid-name
    inputs,
    conv_defs,
    multiplier=1.0,
    final_endpoint=None,
    output_stride=None,
    use_explicit_padding=False,
    scope=None,
    is_training=False):
  """Mobilenet base network.

  Constructs a network from inputs to the given final endpoint. By default
  the network is constructed in inference mode. To create network
  in training mode use:

  with slim.arg_scope(mobilenet.training_scope()):
     logits, endpoints = mobilenet_base(...)

  Args:
    inputs: a tensor of shape [batch_size, height, width, channels].
    conv_defs: A list of op(...) layers specifying the net architecture.
    multiplier: Float multiplier for the depth (number of channels)
      for all convolution ops. The value must be greater than zero. Typical
      usage will be to set this value in (0, 1) to reduce the number of
      parameters or computation cost of the model.
    final_endpoint: The name of last layer, for early termination for
    for V1-based networks: last layer is "layer_14", for V2: "layer_20"
    output_stride: An integer that specifies the requested ratio of input to
      output spatial resolution. If not None, then we invoke atrous convolution
      if necessary to prevent the network from reducing the spatial resolution
      of the activation maps. Allowed values are 1 or any even number, excluding
      zero. Typical values are 8 (accurate fully convolutional mode), 16
      (fast fully convolutional mode), and 32 (classification mode).

      NOTE- output_stride relies on all consequent operators to support dilated
      operators via "rate" parameter. This might require wrapping non-conv
      operators to operate properly.

    use_explicit_padding: Use 'VALID' padding for convolutions, but prepad
      inputs so that the output dimensions are the same as if 'SAME' padding
      were used.
    scope: optional variable scope.
    is_training: How to setup batch_norm and other ops. Note: most of the time
      this does not need be set directly. Use mobilenet.training_scope() to set
      up training instead. This parameter is here for backward compatibility
      only. It is safe to set it to the value matching
      training_scope(is_training=...). It is also safe to explicitly set
      it to False, even if there is outer training_scope set to to training.
      (The network will be built in inference mode). If this is set to None,
      no arg_scope is added for slim.batch_norm's is_training parameter.

  Returns:
    tensor_out: output tensor.
    end_points: a set of activations for external use, for example summaries or
                losses.

  Raises:
    ValueError: depth_multiplier <= 0, or the target output_stride is not
                allowed.
  """
  if multiplier <= 0:
    raise ValueError('multiplier is not greater than zero.')

  # Set conv defs defaults and overrides.
  conv_defs_defaults = conv_defs.get('defaults', {})
  conv_defs_overrides = conv_defs.get('overrides', {})
  if use_explicit_padding:
    conv_defs_overrides = copy.deepcopy(conv_defs_overrides)
    conv_defs_overrides[
        (slim.conv2d, slim.separable_conv2d)] = {'padding': 'VALID'}

  if output_stride is not None:
    if output_stride == 0 or (output_stride > 1 and output_stride % 2):
      raise ValueError('Output stride must be None, 1 or a multiple of 2.')

  # a) Set the tensorflow scope
  # b) set padding to default: note we might consider removing this
  # since it is also set by mobilenet_scope
  # c) set all defaults
  # d) set all extra overrides.
  # pylint: disable=g-backslash-continuation
  with _scope_all(scope, default_scope='Mobilenet'), \
      safe_arg_scope([slim.batch_norm], is_training=is_training), \
      _set_arg_scope_defaults(conv_defs_defaults), \
      _set_arg_scope_defaults(conv_defs_overrides):
    # The current_stride variable keeps track of the output stride of the
    # activations, i.e., the running product of convolution strides up to the
    # current network layer. This allows us to invoke atrous convolution
    # whenever applying the next convolution would result in the activations
    # having output stride larger than the target output_stride.
    current_stride = 1

    # The atrous convolution rate parameter.
    rate = 1

    net = inputs
    # Insert default parameters before the base scope which includes
    # any custom overrides set in mobilenet.
    end_points = {}
    scopes = {}
    for i, opdef in enumerate(conv_defs['spec']):
      params = dict(opdef.params)
      opdef.multiplier_func(params, multiplier)
      stride = params.get('stride', 1)
      if output_stride is not None and current_stride == output_stride:
        # If we have reached the target output_stride, then we need to employ
        # atrous convolution with stride=1 and multiply the atrous rate by the
        # current unit's stride for use in subsequent layers.
        layer_stride = 1
        layer_rate = rate
        rate *= stride
      else:
        layer_stride = stride
        layer_rate = 1
        current_stride *= stride
      # Update params.
      params['stride'] = layer_stride
      # Only insert rate to params if rate > 1 and kernel size is not [1, 1].
      if layer_rate > 1:
        if tuple(params.get('kernel_size', [])) != (1, 1):
          # We will apply atrous rate in the following cases:
          # 1) When kernel_size is not in params, the operation then uses
          #   default kernel size 3x3.
          # 2) When kernel_size is in params, and if the kernel_size is not
          #   equal to (1, 1) (there is no need to apply atrous convolution to
          #   any 1x1 convolution).
          params['rate'] = layer_rate
      # Set padding
      if use_explicit_padding:
        if 'kernel_size' in params:
          net = _fixed_padding(net, params['kernel_size'], layer_rate)
        else:
          params['use_explicit_padding'] = True

      end_point = 'layer_%d' % (i + 1)
      try:
        net = opdef.op(net, **params)
      except Exception:
        print('Failed to create op %i: %r params: %r' % (i, opdef, params))
        raise
      end_points[end_point] = net
      scope = os.path.dirname(net.name)
      scopes[scope] = end_point
      if final_endpoint is not None and end_point == final_endpoint:
        break

    # Add all tensors that end with 'output' to
    # endpoints
    for t in net.graph.get_operations():
      scope = os.path.dirname(t.name)
      bn = os.path.basename(t.name)
      if scope in scopes and t.name.endswith('output'):
        end_points[scopes[scope] + '/' + bn] = t.outputs[0]
    return net, end_points