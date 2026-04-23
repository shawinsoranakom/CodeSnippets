def build_optimizer(
    optimizer_name: Text,
    base_learning_rate: tf_keras.optimizers.schedules.LearningRateSchedule,
    params: Dict[Text, Any],
    model: Optional[tf_keras.Model] = None):
  """Build the optimizer based on name.

  Args:
    optimizer_name: String representation of the optimizer name. Examples: sgd,
      momentum, rmsprop.
    base_learning_rate: `tf_keras.optimizers.schedules.LearningRateSchedule`
      base learning rate.
    params: String -> Any dictionary representing the optimizer params. This
      should contain optimizer specific parameters such as `base_learning_rate`,
      `decay`, etc.
    model: The `tf_keras.Model`. This is used for the shadow copy if using
      `ExponentialMovingAverage`.

  Returns:
    A tf_keras.optimizers.legacy.Optimizer.

  Raises:
    ValueError if the provided optimizer_name is not supported.

  """
  optimizer_name = optimizer_name.lower()
  logging.info('Building %s optimizer with params %s', optimizer_name, params)

  if optimizer_name == 'sgd':
    logging.info('Using SGD optimizer')
    nesterov = params.get('nesterov', False)
    optimizer = tf_keras.optimizers.legacy.SGD(
        learning_rate=base_learning_rate, nesterov=nesterov)
  elif optimizer_name == 'momentum':
    logging.info('Using momentum optimizer')
    nesterov = params.get('nesterov', False)
    optimizer = tf_keras.optimizers.legacy.SGD(
        learning_rate=base_learning_rate,
        momentum=params['momentum'],
        nesterov=nesterov)
  elif optimizer_name == 'rmsprop':
    logging.info('Using RMSProp')
    rho = params.get('decay', None) or params.get('rho', 0.9)
    momentum = params.get('momentum', 0.9)
    epsilon = params.get('epsilon', 1e-07)
    optimizer = tf_keras.optimizers.legacy.RMSprop(
        learning_rate=base_learning_rate,
        rho=rho,
        momentum=momentum,
        epsilon=epsilon)
  elif optimizer_name == 'adam':
    logging.info('Using Adam')
    beta_1 = params.get('beta_1', 0.9)
    beta_2 = params.get('beta_2', 0.999)
    epsilon = params.get('epsilon', 1e-07)
    optimizer = tf_keras.optimizers.legacy.Adam(
        learning_rate=base_learning_rate,
        beta_1=beta_1,
        beta_2=beta_2,
        epsilon=epsilon)
  elif optimizer_name == 'adamw':
    logging.info('Using AdamW')
    weight_decay = params.get('weight_decay', 0.01)
    beta_1 = params.get('beta_1', 0.9)
    beta_2 = params.get('beta_2', 0.999)
    epsilon = params.get('epsilon', 1e-07)
    optimizer = legacy_adamw.AdamWeightDecay(
        learning_rate=base_learning_rate,
        weight_decay_rate=weight_decay,
        beta_1=beta_1,
        beta_2=beta_2,
        epsilon=epsilon,
    )
  else:
    raise ValueError('Unknown optimizer %s' % optimizer_name)

  if params.get('lookahead', None):
    logging.info('Using lookahead optimizer.')
    optimizer = Lookahead(optimizer)

  # Moving average should be applied last, as it's applied at test time
  moving_average_decay = params.get('moving_average_decay', 0.)
  if moving_average_decay is not None and moving_average_decay > 0.:
    if model is None:
      raise ValueError(
          '`model` must be provided if using `ExponentialMovingAverage`.')
    logging.info('Including moving average decay.')
    optimizer = optimization.ExponentialMovingAverage(
        optimizer=optimizer, average_decay=moving_average_decay)
    optimizer.shadow_copy(model)
  return optimizer