def build_optimizer(
      self,
      lr: Union[tf_keras.optimizers.schedules.LearningRateSchedule, float],
      gradient_aggregator: Optional[Callable[
          [List[Tuple[tf.Tensor, tf.Tensor]]], List[Tuple[tf.Tensor,
                                                          tf.Tensor]]]] = None,
      gradient_transformers: Optional[List[Callable[
          [List[Tuple[tf.Tensor, tf.Tensor]]], List[Tuple[tf.Tensor,
                                                          tf.Tensor]]]]] = None,
      postprocessor: Optional[Callable[[tf_keras.optimizers.Optimizer],
                                       tf_keras.optimizers.Optimizer]] = None,
      use_legacy_optimizer: bool = True):
    """Build optimizer.

    Builds optimizer from config. It takes learning rate as input, and builds
    the optimizer according to the optimizer config. Typically, the learning
    rate built using self.build_lr() is passed as an argument to this method.

    Args:
      lr: A floating point value, or a
        tf_keras.optimizers.schedules.LearningRateSchedule instance.
      gradient_aggregator: Optional function to overwrite gradient aggregation.
      gradient_transformers: Optional list of functions to use to transform
        gradients before applying updates to Variables. The functions are
        applied after gradient_aggregator. The functions should accept and
        return a list of (gradient, variable) tuples. clipvalue, clipnorm,
        global_clipnorm should not be set when gradient_transformers is passed.
      postprocessor: An optional function for postprocessing the optimizer. It
        takes an optimizer and returns an optimizer.
      use_legacy_optimizer: A boolean that indicates if using legacy optimizers.

    Returns:
      `tf_keras.optimizers.legacy.Optimizer` or
      `tf_keras.optimizers.experimental.Optimizer` instance.
    """

    optimizer_dict = self._optimizer_config.as_dict()
    ## Delete clipnorm, clipvalue, global_clipnorm if None
    if optimizer_dict['clipnorm'] is None:
      del optimizer_dict['clipnorm']
    if optimizer_dict['clipvalue'] is None:
      del optimizer_dict['clipvalue']
    if optimizer_dict['global_clipnorm'] is None:
      del optimizer_dict['global_clipnorm']

    optimizer_dict['learning_rate'] = lr
    if gradient_aggregator is not None:
      optimizer_dict['gradient_aggregator'] = gradient_aggregator
    if gradient_transformers is not None:
      optimizer_dict['gradient_transformers'] = gradient_transformers

    if use_legacy_optimizer:
      optimizer = LEGACY_OPTIMIZERS_CLS[self._optimizer_type](**optimizer_dict)
    else:
      if 'decay' in optimizer_dict:
        raise ValueError(
            '`decay` is deprecated in new Keras optimizer, please reflect the '
            'decay logic in `lr` or set `use_legacy_optimizer=True` to use the '
            'legacy optimizer.')
      optimizer = NEW_OPTIMIZERS_CLS[self._optimizer_type](**optimizer_dict)

    if self._use_ema:
      if not use_legacy_optimizer:
        raise ValueError(
            'EMA can only work with the legacy optimizer, please set '
            '`use_legacy_optimizer=True`.')
      optimizer = ema_optimizer.ExponentialMovingAverage(
          optimizer, **self._ema_config.as_dict())
    if postprocessor:
      optimizer = postprocessor(optimizer)
    if isinstance(optimizer, tf_keras.optimizers.Optimizer):
      return optimizer
    # The following check makes sure the function won't break in older TF
    # version because of missing the experimental/legacy package.
    if hasattr(tf_keras.optimizers, 'experimental'):
      if isinstance(optimizer, tf_keras.optimizers.experimental.Optimizer):
        return optimizer
    if hasattr(tf_keras.optimizers, 'legacy'):
      if isinstance(optimizer, tf_keras.optimizers.legacy.Optimizer):
        return optimizer
    raise TypeError('OptimizerFactory.build_optimizer returning a '
                    'non-optimizer object: {}'.format(optimizer))