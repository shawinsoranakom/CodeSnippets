def run_training(train_op,
                 loss,
                 global_step,
                 variables_to_restore=None,
                 pretrained_model_dir=None):
  """Sets up and runs training loop."""
  tf.gfile.MakeDirs(FLAGS.train_dir)

  # Create pretrain Saver
  if pretrained_model_dir:
    assert variables_to_restore
    tf.logging.info('Will attempt restore from %s: %s', pretrained_model_dir,
                    variables_to_restore)
    saver_for_restore = tf.train.Saver(variables_to_restore)

  # Init ops
  if FLAGS.sync_replicas:
    local_init_op = tf.get_collection('local_init_op')[0]
    ready_for_local_init_op = tf.get_collection('ready_for_local_init_op')[0]
  else:
    local_init_op = tf.train.Supervisor.USE_DEFAULT
    ready_for_local_init_op = tf.train.Supervisor.USE_DEFAULT

  is_chief = FLAGS.task == 0
  sv = tf.train.Supervisor(
      logdir=FLAGS.train_dir,
      is_chief=is_chief,
      save_summaries_secs=30,
      save_model_secs=30,
      local_init_op=local_init_op,
      ready_for_local_init_op=ready_for_local_init_op,
      global_step=global_step)

  # Delay starting standard services to allow possible pretrained model restore.
  with sv.managed_session(
      master=FLAGS.master,
      config=tf.ConfigProto(log_device_placement=FLAGS.log_device_placement),
      start_standard_services=False) as sess:
    # Initialization
    if is_chief:
      if pretrained_model_dir:
        maybe_restore_pretrained_model(sess, saver_for_restore,
                                       pretrained_model_dir)
      if FLAGS.sync_replicas:
        sess.run(tf.get_collection('chief_init_op')[0])
      sv.start_standard_services(sess)

    sv.start_queue_runners(sess)

    # Training loop
    global_step_val = 0
    while not sv.should_stop() and global_step_val < FLAGS.max_steps:
      global_step_val = train_step(sess, train_op, loss, global_step)

    # Final checkpoint
    if is_chief and global_step_val >= FLAGS.max_steps:
      sv.saver.save(sess, sv.save_path, global_step=global_step)