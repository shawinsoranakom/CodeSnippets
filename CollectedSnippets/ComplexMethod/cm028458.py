def build_learning_rate(params: base_configs.LearningRateConfig,
                        batch_size: Optional[int] = None,
                        train_epochs: Optional[int] = None,
                        train_steps: Optional[int] = None):
  """Build the learning rate given the provided configuration."""
  decay_type = params.name
  base_lr = params.initial_lr
  decay_rate = params.decay_rate
  if params.decay_epochs is not None:
    decay_steps = params.decay_epochs * train_steps
  else:
    decay_steps = 0
  if params.warmup_epochs is not None:
    warmup_steps = params.warmup_epochs * train_steps
  else:
    warmup_steps = 0

  lr_multiplier = params.scale_by_batch_size

  if lr_multiplier and lr_multiplier > 0:
    # Scale the learning rate based on the batch size and a multiplier
    base_lr *= lr_multiplier * batch_size
    logging.info(
        'Scaling the learning rate based on the batch size '
        'multiplier. New base_lr: %f', base_lr)

  if decay_type == 'exponential':
    logging.info(
        'Using exponential learning rate with: '
        'initial_learning_rate: %f, decay_steps: %d, '
        'decay_rate: %f', base_lr, decay_steps, decay_rate)
    lr = tf_keras.optimizers.schedules.ExponentialDecay(
        initial_learning_rate=base_lr,
        decay_steps=decay_steps,
        decay_rate=decay_rate,
        staircase=params.staircase)
  elif decay_type == 'stepwise':
    steps_per_epoch = params.examples_per_epoch // batch_size
    boundaries = [boundary * steps_per_epoch for boundary in params.boundaries]
    multipliers = [batch_size * multiplier for multiplier in params.multipliers]
    logging.info(
        'Using stepwise learning rate. Parameters: '
        'boundaries: %s, values: %s', boundaries, multipliers)
    lr = tf_keras.optimizers.schedules.PiecewiseConstantDecay(
        boundaries=boundaries, values=multipliers)
  elif decay_type == 'cosine_with_warmup':
    lr = learning_rate.CosineDecayWithWarmup(
        batch_size=batch_size,
        total_steps=train_epochs * train_steps,
        warmup_steps=warmup_steps)
  if warmup_steps > 0:
    if decay_type not in ['cosine_with_warmup']:
      logging.info('Applying %d warmup steps to the learning rate',
                   warmup_steps)
      lr = learning_rate.WarmupDecaySchedule(
          lr, warmup_steps, warmup_lr=base_lr)
  return lr