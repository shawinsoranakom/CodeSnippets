def deploy(config,
           model_fn,
           args=None,
           kwargs=None,
           optimizer=None,
           summarize_gradients=False):
  """Deploys a Slim-constructed model across multiple clones.

  The deployment options are specified by the config object and support
  deploying one or several clones on different GPUs and one or several replicas
  of such clones.

  The argument `model_fn` is called `config.num_clones` times to create the
  model clones as `model_fn(*args, **kwargs)`.

  The optional argument `optimizer` is an `Optimizer` object.  If not `None`,
  the deployed model is configured for training with that optimizer.

  If `config` specifies deployment on multiple replicas then the default
  tensorflow device is set appropriatly for each call to `model_fn` and for the
  slim variable creation functions: model and global variables will be created
  on the `ps` device, the clone operations will be on the `worker` device.

  Args:
    config: A `DeploymentConfig` object.
    model_fn: A callable. Called as `model_fn(*args, **kwargs)`
    args: Optional list of arguments to pass to `model_fn`.
    kwargs: Optional list of keyword arguments to pass to `model_fn`.
    optimizer: Optional `Optimizer` object.  If passed the model is deployed
      for training with that optimizer.
    summarize_gradients: Whether or not add summaries to the gradients.

  Returns:
    A `DeployedModel` namedtuple.

  """
  # Gather initial summaries.
  summaries = set(tf.get_collection(tf.GraphKeys.SUMMARIES))

  # Create Clones.
  clones = create_clones(config, model_fn, args, kwargs)
  first_clone = clones[0]

  # Gather update_ops from the first clone. These contain, for example,
  # the updates for the batch_norm variables created by model_fn.
  update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, first_clone.scope)

  train_op = None
  total_loss = None
  with tf.device(config.optimizer_device()):
    if optimizer:
      # Place the global step on the device storing the variables.
      with tf.device(config.variables_device()):
        global_step = slim.get_or_create_global_step()

      # Compute the gradients for the clones.
      total_loss, clones_gradients = optimize_clones(clones, optimizer)

      if clones_gradients:
        if summarize_gradients:
          # Add summaries to the gradients.
          summaries |= set(_add_gradients_summaries(clones_gradients))

        # Create gradient updates.
        grad_updates = optimizer.apply_gradients(clones_gradients,
                                                 global_step=global_step)
        update_ops.append(grad_updates)

        update_op = tf.group(*update_ops)
        with tf.control_dependencies([update_op]):
          train_op = tf.identity(total_loss, name='train_op')
    else:
      clones_losses = []
      regularization_losses = tf.get_collection(
          tf.GraphKeys.REGULARIZATION_LOSSES)
      for clone in clones:
        with tf.name_scope(clone.scope):
          clone_loss = _gather_clone_loss(clone, len(clones),
                                          regularization_losses)
          if clone_loss is not None:
            clones_losses.append(clone_loss)
          # Only use regularization_losses for the first clone
          regularization_losses = None
      if clones_losses:
        total_loss = tf.add_n(clones_losses, name='total_loss')

    # Add the summaries from the first clone. These contain the summaries
    # created by model_fn and either optimize_clones() or _gather_clone_loss().
    summaries |= set(tf.get_collection(tf.GraphKeys.SUMMARIES,
                                       first_clone.scope))

    if total_loss is not None:
      # Add total_loss to summary.
      summaries.add(tf.summary.scalar('total_loss', total_loss))

    if summaries:
      # Merge all summaries together.
      summary_op = tf.summary.merge(list(summaries), name='summary_op')
    else:
      summary_op = None

  return DeployedModel(train_op, summary_op, total_loss, clones)