def get_model_learning_rate(learning_policy,
                            base_learning_rate,
                            learning_rate_decay_step,
                            learning_rate_decay_factor,
                            training_number_of_steps,
                            learning_power,
                            slow_start_step,
                            slow_start_learning_rate,
                            slow_start_burnin_type='none',
                            decay_steps=0.0,
                            end_learning_rate=0.0,
                            boundaries=None,
                            boundary_learning_rates=None):
  """Gets model's learning rate.

  Computes the model's learning rate for different learning policy.
  Right now, only "step" and "poly" are supported.
  (1) The learning policy for "step" is computed as follows:
    current_learning_rate = base_learning_rate *
      learning_rate_decay_factor ^ (global_step / learning_rate_decay_step)
  See tf.train.exponential_decay for details.
  (2) The learning policy for "poly" is computed as follows:
    current_learning_rate = base_learning_rate *
      (1 - global_step / training_number_of_steps) ^ learning_power

  Args:
    learning_policy: Learning rate policy for training.
    base_learning_rate: The base learning rate for model training.
    learning_rate_decay_step: Decay the base learning rate at a fixed step.
    learning_rate_decay_factor: The rate to decay the base learning rate.
    training_number_of_steps: Number of steps for training.
    learning_power: Power used for 'poly' learning policy.
    slow_start_step: Training model with small learning rate for the first
      few steps.
    slow_start_learning_rate: The learning rate employed during slow start.
    slow_start_burnin_type: The burnin type for the slow start stage. Can be
      `none` which means no burnin or `linear` which means the learning rate
      increases linearly from slow_start_learning_rate and reaches
      base_learning_rate after slow_start_steps.
    decay_steps: Float, `decay_steps` for polynomial learning rate.
    end_learning_rate: Float, `end_learning_rate` for polynomial learning rate.
    boundaries: A list of `Tensor`s or `int`s or `float`s with strictly
      increasing entries.
    boundary_learning_rates: A list of `Tensor`s or `float`s or `int`s that
      specifies the values for the intervals defined by `boundaries`. It should
      have one more element than `boundaries`, and all elements should have the
      same type.

  Returns:
    Learning rate for the specified learning policy.

  Raises:
    ValueError: If learning policy or slow start burnin type is not recognized.
    ValueError: If `boundaries` and `boundary_learning_rates` are not set for
      multi_steps learning rate decay.
  """
  global_step = tf.train.get_or_create_global_step()
  adjusted_global_step = tf.maximum(global_step - slow_start_step, 0)
  if decay_steps == 0.0:
    tf.logging.info('Setting decay_steps to total training steps.')
    decay_steps = training_number_of_steps - slow_start_step
  if learning_policy == 'step':
    learning_rate = tf.train.exponential_decay(
        base_learning_rate,
        adjusted_global_step,
        learning_rate_decay_step,
        learning_rate_decay_factor,
        staircase=True)
  elif learning_policy == 'poly':
    learning_rate = tf.train.polynomial_decay(
        base_learning_rate,
        adjusted_global_step,
        decay_steps=decay_steps,
        end_learning_rate=end_learning_rate,
        power=learning_power)
  elif learning_policy == 'cosine':
    learning_rate = tf.train.cosine_decay(
        base_learning_rate,
        adjusted_global_step,
        training_number_of_steps - slow_start_step)
  elif learning_policy == 'multi_steps':
    if boundaries is None or boundary_learning_rates is None:
      raise ValueError('Must set `boundaries` and `boundary_learning_rates` '
                       'for multi_steps learning rate decay.')
    learning_rate = tf.train.piecewise_constant_decay(
        adjusted_global_step,
        boundaries,
        boundary_learning_rates)
  else:
    raise ValueError('Unknown learning policy.')

  adjusted_slow_start_learning_rate = slow_start_learning_rate
  if slow_start_burnin_type == 'linear':
    # Do linear burnin. Increase linearly from slow_start_learning_rate and
    # reach base_learning_rate after (global_step >= slow_start_steps).
    adjusted_slow_start_learning_rate = (
        slow_start_learning_rate +
        (base_learning_rate - slow_start_learning_rate) *
        tf.to_float(global_step) / slow_start_step)
  elif slow_start_burnin_type != 'none':
    raise ValueError('Unknown burnin type.')

  # Employ small learning rate at the first few steps for warm start.
  return tf.where(global_step < slow_start_step,
                  adjusted_slow_start_learning_rate, learning_rate)