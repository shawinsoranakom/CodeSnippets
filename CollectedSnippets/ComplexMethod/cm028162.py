def run(self):
    """Run training."""
    is_chief = FLAGS.task_id == 0 or not FLAGS.supervisor
    sv = None

    def init_fn(sess, saver):
      ckpt = None
      if FLAGS.save_dir and sv is None:
        load_dir = FLAGS.save_dir
        ckpt = tf.train.get_checkpoint_state(load_dir)
      if ckpt and ckpt.model_checkpoint_path:
        logging.info('restoring from %s', ckpt.model_checkpoint_path)
        saver.restore(sess, ckpt.model_checkpoint_path)
      elif FLAGS.load_path:
        logging.info('restoring from %s', FLAGS.load_path)
        saver.restore(sess, FLAGS.load_path)

    if FLAGS.supervisor:
      with tf.device(tf.ReplicaDeviceSetter(FLAGS.ps_tasks, merge_devices=True)):
        self.global_step = tf.contrib.framework.get_or_create_global_step()
        tf.set_random_seed(FLAGS.tf_seed)
        self.controller = self.get_controller(self.env)
        self.model = self.controller.model
        self.controller.setup()
        with tf.variable_scope(tf.get_variable_scope(), reuse=True):
          self.eval_controller = self.get_controller(self.eval_env)
          self.eval_controller.setup(train=False)

        saver = tf.train.Saver(max_to_keep=10)
        step = self.model.global_step
        sv = tf.Supervisor(logdir=FLAGS.save_dir,
                           is_chief=is_chief,
                           saver=saver,
                           save_model_secs=600,
                           summary_op=None,  # we define it ourselves
                           save_summaries_secs=60,
                           global_step=step,
                           init_fn=lambda sess: init_fn(sess, saver))
        sess = sv.PrepareSession(FLAGS.master)
    else:
      tf.set_random_seed(FLAGS.tf_seed)
      self.global_step = tf.contrib.framework.get_or_create_global_step()
      self.controller = self.get_controller(self.env)
      self.model = self.controller.model
      self.controller.setup()
      with tf.variable_scope(tf.get_variable_scope(), reuse=True):
        self.eval_controller = self.get_controller(self.eval_env)
        self.eval_controller.setup(train=False)

      saver = tf.train.Saver(max_to_keep=10)
      sess = tf.Session()
      sess.run(tf.initialize_all_variables())
      init_fn(sess, saver)

    self.sv = sv
    self.sess = sess

    logging.info('hparams:\n%s', self.hparams_string())

    model_step = sess.run(self.model.global_step)
    if model_step >= self.num_steps:
      logging.info('training has reached final step')
      return

    losses = []
    rewards = []
    all_ep_rewards = []
    for step in xrange(1 + self.num_steps):

      if sv is not None and sv.ShouldStop():
        logging.info('stopping supervisor')
        break

      self.do_before_step(step)

      (loss, summary,
       total_rewards, episode_rewards) = self.controller.train(sess)
      _, greedy_episode_rewards = self.eval_controller.eval(sess)
      self.controller.greedy_episode_rewards = greedy_episode_rewards
      losses.append(loss)
      rewards.append(total_rewards)
      all_ep_rewards.extend(episode_rewards)

      if (random.random() < 0.1 and summary and episode_rewards and
          is_chief and sv and sv._summary_writer):
        sv.summary_computed(sess, summary)

      model_step = sess.run(self.model.global_step)
      if is_chief and step % self.validation_frequency == 0:
        logging.info('at training step %d, model step %d: '
                     'avg loss %f, avg reward %f, '
                     'episode rewards: %f, greedy rewards: %f',
                     step, model_step,
                     np.mean(losses), np.mean(rewards),
                     np.mean(all_ep_rewards),
                     np.mean(greedy_episode_rewards))

        losses = []
        rewards = []
        all_ep_rewards = []

      if model_step >= self.num_steps:
        logging.info('training has reached final step')
        break

    if is_chief and sv is not None:
      logging.info('saving final model to %s', sv.save_path)
      sv.saver.save(sess, sv.save_path, global_step=sv.global_step)