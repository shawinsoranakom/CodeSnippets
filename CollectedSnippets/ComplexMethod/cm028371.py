def train(train_model, pretrained_ckpt, checkpoint_dir, train_steps,
          summary_freq):
  """Train model."""
  if pretrained_ckpt is not None:
    vars_to_restore = util.get_vars_to_restore(pretrained_ckpt)
    pretrain_restorer = tf.train.Saver(vars_to_restore)
  vars_to_save = util.get_vars_to_restore()
  saver = tf.train.Saver(vars_to_save + [train_model.global_step],
                         max_to_keep=MAX_TO_KEEP)
  sv = tf.train.Supervisor(logdir=checkpoint_dir, save_summaries_secs=0,
                           saver=None)
  config = tf.ConfigProto()
  config.gpu_options.allow_growth = True
  with sv.managed_session(config=config) as sess:
    if pretrained_ckpt is not None:
      logging.info('Restoring pretrained weights from %s', pretrained_ckpt)
      pretrain_restorer.restore(sess, pretrained_ckpt)
    logging.info('Attempting to resume training from %s...', checkpoint_dir)
    checkpoint = tf.train.latest_checkpoint(checkpoint_dir)
    logging.info('Last checkpoint found: %s', checkpoint)
    if checkpoint:
      saver.restore(sess, checkpoint)

    logging.info('Training...')
    start_time = time.time()
    last_summary_time = time.time()
    steps_per_epoch = train_model.reader.steps_per_epoch
    step = 1
    while step <= train_steps:
      fetches = {
          'train': train_model.train_op,
          'global_step': train_model.global_step,
          'incr_global_step': train_model.incr_global_step
      }

      if step % summary_freq == 0:
        fetches['loss'] = train_model.total_loss
        fetches['summary'] = sv.summary_op

      results = sess.run(fetches)
      global_step = results['global_step']

      if step % summary_freq == 0:
        sv.summary_writer.add_summary(results['summary'], global_step)
        train_epoch = math.ceil(global_step / steps_per_epoch)
        train_step = global_step - (train_epoch - 1) * steps_per_epoch
        this_cycle = time.time() - last_summary_time
        last_summary_time += this_cycle
        logging.info(
            'Epoch: [%2d] [%5d/%5d] time: %4.2fs (%ds total) loss: %.3f',
            train_epoch, train_step, steps_per_epoch, this_cycle,
            time.time() - start_time, results['loss'])

      if step % steps_per_epoch == 0:
        logging.info('[*] Saving checkpoint to %s...', checkpoint_dir)
        saver.save(sess, os.path.join(checkpoint_dir, 'model'),
                   global_step=global_step)

      # Setting step to global_step allows for training for a total of
      # train_steps even if the program is restarted during training.
      step = global_step + 1