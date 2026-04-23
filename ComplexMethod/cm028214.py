def train(create_tensor_dict_fn,
          create_model_fn,
          train_config,
          master,
          task,
          num_clones,
          worker_replicas,
          clone_on_cpu,
          ps_tasks,
          worker_job_name,
          is_chief,
          train_dir,
          graph_hook_fn=None):
  """Training function for detection models.

  Args:
    create_tensor_dict_fn: a function to create a tensor input dictionary.
    create_model_fn: a function that creates a DetectionModel and generates
                     losses.
    train_config: a train_pb2.TrainConfig protobuf.
    master: BNS name of the TensorFlow master to use.
    task: The task id of this training instance.
    num_clones: The number of clones to run per machine.
    worker_replicas: The number of work replicas to train with.
    clone_on_cpu: True if clones should be forced to run on CPU.
    ps_tasks: Number of parameter server tasks.
    worker_job_name: Name of the worker job.
    is_chief: Whether this replica is the chief replica.
    train_dir: Directory to write checkpoints and training summaries to.
    graph_hook_fn: Optional function that is called after the inference graph is
      built (before optimization). This is helpful to perform additional changes
      to the training graph such as adding FakeQuant ops. The function should
      modify the default graph.

  Raises:
    ValueError: If both num_clones > 1 and train_config.sync_replicas is true.
  """

  detection_model = create_model_fn()
  data_augmentation_options = [
      preprocessor_builder.build(step)
      for step in train_config.data_augmentation_options]

  with tf.Graph().as_default():
    # Build a configuration specifying multi-GPU and multi-replicas.
    deploy_config = model_deploy.DeploymentConfig(
        num_clones=num_clones,
        clone_on_cpu=clone_on_cpu,
        replica_id=task,
        num_replicas=worker_replicas,
        num_ps_tasks=ps_tasks,
        worker_job_name=worker_job_name)

    # Place the global step on the device storing the variables.
    with tf.device(deploy_config.variables_device()):
      global_step = slim.create_global_step()

    if num_clones != 1 and train_config.sync_replicas:
      raise ValueError('In Synchronous SGD mode num_clones must ',
                       'be 1. Found num_clones: {}'.format(num_clones))
    batch_size = train_config.batch_size // num_clones
    if train_config.sync_replicas:
      batch_size //= train_config.replicas_to_aggregate

    with tf.device(deploy_config.inputs_device()):
      input_queue = create_input_queue(
          batch_size, create_tensor_dict_fn,
          train_config.batch_queue_capacity,
          train_config.num_batch_queue_threads,
          train_config.prefetch_queue_capacity, data_augmentation_options)

    # Gather initial summaries.
    # TODO(rathodv): See if summaries can be added/extracted from global tf
    # collections so that they don't have to be passed around.
    summaries = set(tf.get_collection(tf.GraphKeys.SUMMARIES))
    global_summaries = set([])

    model_fn = functools.partial(_create_losses,
                                 create_model_fn=create_model_fn,
                                 train_config=train_config)
    clones = model_deploy.create_clones(deploy_config, model_fn, [input_queue])
    first_clone_scope = clones[0].scope

    if graph_hook_fn:
      with tf.device(deploy_config.variables_device()):
        graph_hook_fn()

    # Gather update_ops from the first clone. These contain, for example,
    # the updates for the batch_norm variables created by model_fn.
    update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, first_clone_scope)

    with tf.device(deploy_config.optimizer_device()):
      training_optimizer, optimizer_summary_vars = optimizer_builder.build(
          train_config.optimizer)
      for var in optimizer_summary_vars:
        tf.summary.scalar(var.op.name, var, family='LearningRate')

    sync_optimizer = None
    if train_config.sync_replicas:
      training_optimizer = tf.train.SyncReplicasOptimizer(
          training_optimizer,
          replicas_to_aggregate=train_config.replicas_to_aggregate,
          total_num_replicas=worker_replicas)
      sync_optimizer = training_optimizer

    with tf.device(deploy_config.optimizer_device()):
      regularization_losses = (None if train_config.add_regularization_loss
                               else [])
      total_loss, grads_and_vars = model_deploy.optimize_clones(
          clones, training_optimizer,
          regularization_losses=regularization_losses)
      total_loss = tf.check_numerics(total_loss, 'LossTensor is inf or nan.')

      # Optionally multiply bias gradients by train_config.bias_grad_multiplier.
      if train_config.bias_grad_multiplier:
        biases_regex_list = ['.*/biases']
        grads_and_vars = variables_helper.multiply_gradients_matching_regex(
            grads_and_vars,
            biases_regex_list,
            multiplier=train_config.bias_grad_multiplier)

      # Optionally freeze some layers by setting their gradients to be zero.
      if train_config.freeze_variables:
        grads_and_vars = variables_helper.freeze_gradients_matching_regex(
            grads_and_vars, train_config.freeze_variables)

      # Optionally clip gradients
      if train_config.gradient_clipping_by_norm > 0:
        with tf.name_scope('clip_grads'):
          grads_and_vars = slim.learning.clip_gradient_norms(
              grads_and_vars, train_config.gradient_clipping_by_norm)

      # Create gradient updates.
      grad_updates = training_optimizer.apply_gradients(grads_and_vars,
                                                        global_step=global_step)
      update_ops.append(grad_updates)
      update_op = tf.group(*update_ops, name='update_barrier')
      with tf.control_dependencies([update_op]):
        train_tensor = tf.identity(total_loss, name='train_op')

    # Add summaries.
    for model_var in slim.get_model_variables():
      global_summaries.add(tf.summary.histogram('ModelVars/' +
                                                model_var.op.name, model_var))
    for loss_tensor in tf.losses.get_losses():
      global_summaries.add(tf.summary.scalar('Losses/' + loss_tensor.op.name,
                                             loss_tensor))
    global_summaries.add(
        tf.summary.scalar('Losses/TotalLoss', tf.losses.get_total_loss()))

    # Add the summaries from the first clone. These contain the summaries
    # created by model_fn and either optimize_clones() or _gather_clone_loss().
    summaries |= set(tf.get_collection(tf.GraphKeys.SUMMARIES,
                                       first_clone_scope))
    summaries |= global_summaries

    # Merge all summaries together.
    summary_op = tf.summary.merge(list(summaries), name='summary_op')

    # Soft placement allows placing on CPU ops without GPU implementation.
    session_config = tf.ConfigProto(allow_soft_placement=True,
                                    log_device_placement=False)

    # Save checkpoints regularly.
    keep_checkpoint_every_n_hours = train_config.keep_checkpoint_every_n_hours
    saver = tf.train.Saver(
        keep_checkpoint_every_n_hours=keep_checkpoint_every_n_hours)

    # Create ops required to initialize the model from a given checkpoint.
    init_fn = None
    if train_config.fine_tune_checkpoint:
      if not train_config.fine_tune_checkpoint_type:
        # train_config.from_detection_checkpoint field is deprecated. For
        # backward compatibility, fine_tune_checkpoint_type is set based on
        # from_detection_checkpoint.
        if train_config.from_detection_checkpoint:
          train_config.fine_tune_checkpoint_type = 'detection'
        else:
          train_config.fine_tune_checkpoint_type = 'classification'
      var_map = detection_model.restore_map(
          fine_tune_checkpoint_type=train_config.fine_tune_checkpoint_type,
          load_all_detection_checkpoint_vars=(
              train_config.load_all_detection_checkpoint_vars))
      available_var_map = (variables_helper.
                           get_variables_available_in_checkpoint(
                               var_map, train_config.fine_tune_checkpoint,
                               include_global_step=False))
      init_saver = tf.train.Saver(available_var_map)
      def initializer_fn(sess):
        init_saver.restore(sess, train_config.fine_tune_checkpoint)
      init_fn = initializer_fn

    slim.learning.train(
        train_tensor,
        logdir=train_dir,
        master=master,
        is_chief=is_chief,
        session_config=session_config,
        startup_delay_steps=train_config.startup_delay_steps,
        init_fn=init_fn,
        summary_op=summary_op,
        number_of_steps=(
            train_config.num_steps if train_config.num_steps else None),
        save_summaries_secs=120,
        sync_optimizer=sync_optimizer,
        saver=saver)