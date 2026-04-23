def build(hyperparams_config, is_training):
  """Builds tf-slim arg_scope for convolution ops based on the config.

  Returns an arg_scope to use for convolution ops containing weights
  initializer, weights regularizer, activation function, batch norm function
  and batch norm parameters based on the configuration.

  Note that if no normalization parameters are specified in the config,
  (i.e. left to default) then both batch norm and group norm are excluded
  from the arg_scope.

  The batch norm parameters are set for updates based on `is_training` argument
  and conv_hyperparams_config.batch_norm.train parameter. During training, they
  are updated only if batch_norm.train parameter is true. However, during eval,
  no updates are made to the batch norm variables. In both cases, their current
  values are used during forward pass.

  Args:
    hyperparams_config: hyperparams.proto object containing
      hyperparameters.
    is_training: Whether the network is in training mode.

  Returns:
    arg_scope_fn: A function to construct tf-slim arg_scope containing
      hyperparameters for ops.

  Raises:
    ValueError: if hyperparams_config is not of type hyperparams.Hyperparams.
  """
  if not isinstance(hyperparams_config,
                    hyperparams_pb2.Hyperparams):
    raise ValueError('hyperparams_config not of type '
                     'hyperparams_pb.Hyperparams.')

  if hyperparams_config.force_use_bias:
    raise ValueError('Hyperparams force_use_bias only supported by '
                     'KerasLayerHyperparams.')

  if hyperparams_config.HasField('sync_batch_norm'):
    raise ValueError('Hyperparams sync_batch_norm only supported by '
                     'KerasLayerHyperparams.')

  normalizer_fn = None
  batch_norm_params = None
  if hyperparams_config.HasField('batch_norm'):
    normalizer_fn = slim.batch_norm
    batch_norm_params = _build_batch_norm_params(
        hyperparams_config.batch_norm, is_training)
  if hyperparams_config.HasField('group_norm'):
    normalizer_fn = slim.group_norm
  affected_ops = [slim.conv2d, slim.separable_conv2d, slim.conv2d_transpose]
  if hyperparams_config.HasField('op') and (
      hyperparams_config.op == hyperparams_pb2.Hyperparams.FC):
    affected_ops = [slim.fully_connected]
  def scope_fn():
    with (slim.arg_scope([slim.batch_norm], **batch_norm_params)
          if batch_norm_params is not None else
          context_manager.IdentityContextManager()):
      with slim.arg_scope(
          affected_ops,
          weights_regularizer=_build_slim_regularizer(
              hyperparams_config.regularizer),
          weights_initializer=_build_initializer(
              hyperparams_config.initializer),
          activation_fn=_build_activation_fn(hyperparams_config.activation),
          normalizer_fn=normalizer_fn) as sc:
        return sc

  return scope_fn