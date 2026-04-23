def _update_initial_learning_rate(configs, learning_rate):
  """Updates `configs` to reflect the new initial learning rate.

  This function updates the initial learning rate. For learning rate schedules,
  all other defined learning rates in the pipeline config are scaled to maintain
  their same ratio with the initial learning rate.
  The configs dictionary is updated in place, and hence not returned.

  Args:
    configs: Dictionary of configuration objects. See outputs from
      get_configs_from_pipeline_file() or get_configs_from_multiple_files().
    learning_rate: Initial learning rate for optimizer.

  Raises:
    TypeError: if optimizer type is not supported, or if learning rate type is
      not supported.
  """

  optimizer_type = get_optimizer_type(configs["train_config"])
  if optimizer_type == "rms_prop_optimizer":
    optimizer_config = configs["train_config"].optimizer.rms_prop_optimizer
  elif optimizer_type == "momentum_optimizer":
    optimizer_config = configs["train_config"].optimizer.momentum_optimizer
  elif optimizer_type == "adam_optimizer":
    optimizer_config = configs["train_config"].optimizer.adam_optimizer
  else:
    raise TypeError("Optimizer %s is not supported." % optimizer_type)

  learning_rate_type = get_learning_rate_type(optimizer_config)
  if learning_rate_type == "constant_learning_rate":
    constant_lr = optimizer_config.learning_rate.constant_learning_rate
    constant_lr.learning_rate = learning_rate
  elif learning_rate_type == "exponential_decay_learning_rate":
    exponential_lr = (
        optimizer_config.learning_rate.exponential_decay_learning_rate)
    exponential_lr.initial_learning_rate = learning_rate
  elif learning_rate_type == "manual_step_learning_rate":
    manual_lr = optimizer_config.learning_rate.manual_step_learning_rate
    original_learning_rate = manual_lr.initial_learning_rate
    learning_rate_scaling = float(learning_rate) / original_learning_rate
    manual_lr.initial_learning_rate = learning_rate
    for schedule in manual_lr.schedule:
      schedule.learning_rate *= learning_rate_scaling
  elif learning_rate_type == "cosine_decay_learning_rate":
    cosine_lr = optimizer_config.learning_rate.cosine_decay_learning_rate
    learning_rate_base = cosine_lr.learning_rate_base
    warmup_learning_rate = cosine_lr.warmup_learning_rate
    warmup_scale_factor = warmup_learning_rate / learning_rate_base
    cosine_lr.learning_rate_base = learning_rate
    cosine_lr.warmup_learning_rate = warmup_scale_factor * learning_rate
  else:
    raise TypeError("Learning rate %s is not supported." % learning_rate_type)