def train_step(self, sess, train_ops, global_step, _):
    """This function will be called at each step of training.

    This represents one step of the DDPG algorithm and can include:
    1. collect a <state, action, reward, next_state> transition
    2. update the target network
    3. train the actor
    4. train the critic

    Args:
      sess: A Tensorflow session.
      train_ops: A DdpgTrainOps tuple of train ops to run.
      global_step: The global step.

    Returns:
      A scalar total loss.
      A boolean should stop.
    """
    start_time = time.time()
    if self.train_op_fn is None:
      self.train_op_fn = sess.make_callable([train_ops.train_op, global_step])
      self.meta_train_op_fn = sess.make_callable([train_ops.meta_train_op, global_step])
      self.collect_fn = sess.make_callable([train_ops.collect_experience_op, global_step])
      self.collect_and_train_fn = sess.make_callable(
          [train_ops.train_op, global_step, train_ops.collect_experience_op])
      self.collect_and_meta_train_fn = sess.make_callable(
          [train_ops.meta_train_op, global_step, train_ops.collect_experience_op])
    for _ in range(self.num_collect_per_update - 1):
      self.collect_fn()
    for _ in range(self.num_updates_per_observation - 1):
      self.train_op_fn()

    total_loss, global_step_val, _ = self.collect_and_train_fn()
    if (global_step_val // self.num_collect_per_meta_update !=
        self.last_global_step_val // self.num_collect_per_meta_update):
      self.meta_train_op_fn()

    time_elapsed = time.time() - start_time
    should_stop = False
    if self.max_number_of_steps:
      should_stop = global_step_val >= self.max_number_of_steps
    if global_step_val != self.last_global_step_val:
      if (self.save_policy_every_n_steps and
          global_step_val // self.save_policy_every_n_steps !=
          self.last_global_step_val // self.save_policy_every_n_steps):
        self.policy_save_fn(sess)

      if (self.log_every_n_steps and
          global_step_val % self.log_every_n_steps == 0):
        tf.logging.info(
            'global step %d: loss = %.4f (%.3f sec/step) (%d steps/sec)',
            global_step_val, total_loss, time_elapsed, 1 / time_elapsed)

    self.last_global_step_val = global_step_val
    stop_early = bool(self.should_stop_early and self.should_stop_early())
    return total_loss, should_stop or stop_early