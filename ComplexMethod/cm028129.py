def mobilenet(input_tensor,
              num_classes=1001,
              depth_multiplier=1.0,
              scope='MobilenetV2',
              conv_defs=None,
              finegrain_classification_mode=False,
              min_depth=None,
              divisible_by=None,
              activation_fn=None,
              **kwargs):
  """Creates mobilenet V2 network.

  Inference mode is created by default. To create training use training_scope
  below.

  with slim.arg_scope(mobilenet_v2.training_scope()):
     logits, endpoints = mobilenet_v2.mobilenet(input_tensor)

  Args:
    input_tensor: The input tensor
    num_classes: number of classes
    depth_multiplier: The multiplier applied to scale number of
    channels in each layer.
    scope: Scope of the operator
    conv_defs: Allows to override default conv def.
    finegrain_classification_mode: When set to True, the model
    will keep the last layer large even for small multipliers. Following
    https://arxiv.org/abs/1801.04381
    suggests that it improves performance for ImageNet-type of problems.
      *Note* ignored if final_endpoint makes the builder exit earlier.
    min_depth: If provided, will ensure that all layers will have that
    many channels after application of depth multiplier.
    divisible_by: If provided will ensure that all layers # channels
    will be divisible by this number.
    activation_fn: Activation function to use, defaults to tf.nn.relu6 if not
      specified.
    **kwargs: passed directly to mobilenet.mobilenet:
      prediction_fn- what prediction function to use.
      reuse-: whether to reuse variables (if reuse set to true, scope
      must be given).
  Returns:
    logits/endpoints pair

  Raises:
    ValueError: On invalid arguments
  """
  if conv_defs is None:
    conv_defs = V2_DEF
  if 'multiplier' in kwargs:
    raise ValueError('mobilenetv2 doesn\'t support generic '
                     'multiplier parameter use "depth_multiplier" instead.')
  if finegrain_classification_mode:
    conv_defs = copy.deepcopy(conv_defs)
    if depth_multiplier < 1:
      conv_defs['spec'][-1].params['num_outputs'] /= depth_multiplier
  if activation_fn:
    conv_defs = copy.deepcopy(conv_defs)
    defaults = conv_defs['defaults']
    conv_defaults = (
        defaults[(slim.conv2d, slim.fully_connected, slim.separable_conv2d)])
    conv_defaults['activation_fn'] = activation_fn

  depth_args = {}
  # NB: do not set depth_args unless they are provided to avoid overriding
  # whatever default depth_multiplier might have thanks to arg_scope.
  if min_depth is not None:
    depth_args['min_depth'] = min_depth
  if divisible_by is not None:
    depth_args['divisible_by'] = divisible_by

  with slim.arg_scope((lib.depth_multiplier,), **depth_args):
    return lib.mobilenet(
        input_tensor,
        num_classes=num_classes,
        conv_defs=conv_defs,
        scope=scope,
        multiplier=depth_multiplier,
        **kwargs)