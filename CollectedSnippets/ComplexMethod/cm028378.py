def main(unused_argv):
  tf.logging.set_verbosity(tf.logging.INFO)
  # Set up deployment (i.e., multi-GPUs and/or multi-replicas).
  config = model_deploy.DeploymentConfig(
      num_clones=FLAGS.num_clones,
      clone_on_cpu=FLAGS.clone_on_cpu,
      replica_id=FLAGS.task,
      num_replicas=FLAGS.num_replicas,
      num_ps_tasks=FLAGS.num_ps_tasks)

  # Split the batch across GPUs.
  assert FLAGS.train_batch_size % config.num_clones == 0, (
      'Training batch size not divisble by number of clones (GPUs).')

  clone_batch_size = FLAGS.train_batch_size // config.num_clones

  tf.gfile.MakeDirs(FLAGS.train_logdir)
  tf.logging.info('Training on %s set', FLAGS.train_split)

  with tf.Graph().as_default() as graph:
    with tf.device(config.inputs_device()):
      dataset = data_generator.Dataset(
          dataset_name=FLAGS.dataset,
          split_name=FLAGS.train_split,
          dataset_dir=FLAGS.dataset_dir,
          batch_size=clone_batch_size,
          crop_size=[int(sz) for sz in FLAGS.train_crop_size],
          min_resize_value=FLAGS.min_resize_value,
          max_resize_value=FLAGS.max_resize_value,
          resize_factor=FLAGS.resize_factor,
          min_scale_factor=FLAGS.min_scale_factor,
          max_scale_factor=FLAGS.max_scale_factor,
          scale_factor_step_size=FLAGS.scale_factor_step_size,
          model_variant=FLAGS.model_variant,
          num_readers=4,
          is_training=True,
          should_shuffle=True,
          should_repeat=True)

    # Create the global step on the device storing the variables.
    with tf.device(config.variables_device()):
      global_step = tf.train.get_or_create_global_step()

      # Define the model and create clones.
      model_fn = _build_deeplab
      model_args = (dataset.get_one_shot_iterator(), {
          common.OUTPUT_TYPE: dataset.num_of_classes
      }, dataset.ignore_label)
      clones = model_deploy.create_clones(config, model_fn, args=model_args)

      # Gather update_ops from the first clone. These contain, for example,
      # the updates for the batch_norm variables created by model_fn.
      first_clone_scope = config.clone_scope(0)
      update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS, first_clone_scope)

    # Gather initial summaries.
    summaries = set(tf.get_collection(tf.GraphKeys.SUMMARIES))

    # Add summaries for model variables.
    for model_var in tf.model_variables():
      summaries.add(tf.summary.histogram(model_var.op.name, model_var))

    # Add summaries for images, labels, semantic predictions
    if FLAGS.save_summaries_images:
      summary_image = graph.get_tensor_by_name(
          ('%s/%s:0' % (first_clone_scope, common.IMAGE)).strip('/'))
      summaries.add(
          tf.summary.image('samples/%s' % common.IMAGE, summary_image))

      first_clone_label = graph.get_tensor_by_name(
          ('%s/%s:0' % (first_clone_scope, common.LABEL)).strip('/'))
      # Scale up summary image pixel values for better visualization.
      pixel_scaling = max(1, 255 // dataset.num_of_classes)
      summary_label = tf.cast(first_clone_label * pixel_scaling, tf.uint8)
      summaries.add(
          tf.summary.image('samples/%s' % common.LABEL, summary_label))

      first_clone_output = graph.get_tensor_by_name(
          ('%s/%s:0' % (first_clone_scope, common.OUTPUT_TYPE)).strip('/'))
      predictions = tf.expand_dims(tf.argmax(first_clone_output, 3), -1)

      summary_predictions = tf.cast(predictions * pixel_scaling, tf.uint8)
      summaries.add(
          tf.summary.image(
              'samples/%s' % common.OUTPUT_TYPE, summary_predictions))

    # Add summaries for losses.
    for loss in tf.get_collection(tf.GraphKeys.LOSSES, first_clone_scope):
      summaries.add(tf.summary.scalar('losses/%s' % loss.op.name, loss))

    # Build the optimizer based on the device specification.
    with tf.device(config.optimizer_device()):
      learning_rate = train_utils.get_model_learning_rate(
          FLAGS.learning_policy,
          FLAGS.base_learning_rate,
          FLAGS.learning_rate_decay_step,
          FLAGS.learning_rate_decay_factor,
          FLAGS.training_number_of_steps,
          FLAGS.learning_power,
          FLAGS.slow_start_step,
          FLAGS.slow_start_learning_rate,
          decay_steps=FLAGS.decay_steps,
          end_learning_rate=FLAGS.end_learning_rate)

      summaries.add(tf.summary.scalar('learning_rate', learning_rate))

      if FLAGS.optimizer == 'momentum':
        optimizer = tf.train.MomentumOptimizer(learning_rate, FLAGS.momentum)
      elif FLAGS.optimizer == 'adam':
        optimizer = tf.train.AdamOptimizer(
            learning_rate=FLAGS.adam_learning_rate, epsilon=FLAGS.adam_epsilon)
      else:
        raise ValueError('Unknown optimizer')

    if FLAGS.quantize_delay_step >= 0:
      if FLAGS.num_clones > 1:
        raise ValueError('Quantization doesn\'t support multi-clone yet.')
      contrib_quantize.create_training_graph(
          quant_delay=FLAGS.quantize_delay_step)

    startup_delay_steps = FLAGS.task * FLAGS.startup_delay_steps

    with tf.device(config.variables_device()):
      total_loss, grads_and_vars = model_deploy.optimize_clones(
          clones, optimizer)
      total_loss = tf.check_numerics(total_loss, 'Loss is inf or nan.')
      summaries.add(tf.summary.scalar('total_loss', total_loss))

      # Modify the gradients for biases and last layer variables.
      last_layers = model.get_extra_layer_scopes(
          FLAGS.last_layers_contain_logits_only)
      grad_mult = train_utils.get_model_gradient_multipliers(
          last_layers, FLAGS.last_layer_gradient_multiplier)
      if grad_mult:
        grads_and_vars = slim.learning.multiply_gradients(
            grads_and_vars, grad_mult)

      # Create gradient update op.
      grad_updates = optimizer.apply_gradients(
          grads_and_vars, global_step=global_step)
      update_ops.append(grad_updates)
      update_op = tf.group(*update_ops)
      with tf.control_dependencies([update_op]):
        train_tensor = tf.identity(total_loss, name='train_op')

    # Add the summaries from the first clone. These contain the summaries
    # created by model_fn and either optimize_clones() or _gather_clone_loss().
    summaries |= set(
        tf.get_collection(tf.GraphKeys.SUMMARIES, first_clone_scope))

    # Merge all summaries together.
    summary_op = tf.summary.merge(list(summaries))

    # Soft placement allows placing on CPU ops without GPU implementation.
    session_config = tf.ConfigProto(
        allow_soft_placement=True, log_device_placement=False)

    # Start the training.
    profile_dir = FLAGS.profile_logdir
    if profile_dir is not None:
      tf.gfile.MakeDirs(profile_dir)

    with contrib_tfprof.ProfileContext(
        enabled=profile_dir is not None, profile_dir=profile_dir):
      init_fn = None
      if FLAGS.tf_initial_checkpoint:
        init_fn = train_utils.get_model_init_fn(
            FLAGS.train_logdir,
            FLAGS.tf_initial_checkpoint,
            FLAGS.initialize_last_layer,
            last_layers,
            ignore_missing_vars=True)

      slim.learning.train(
          train_tensor,
          logdir=FLAGS.train_logdir,
          log_every_n_steps=FLAGS.log_steps,
          master=FLAGS.master,
          number_of_steps=FLAGS.training_number_of_steps,
          is_chief=(FLAGS.task == 0),
          session_config=session_config,
          startup_delay_steps=startup_delay_steps,
          init_fn=init_fn,
          summary_op=summary_op,
          save_summaries_secs=FLAGS.save_summaries_secs,
          save_interval_secs=FLAGS.save_interval_secs)