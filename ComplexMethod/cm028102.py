def _create_train_op(self, grads_and_vars, extra_grads_and_vars=[]):
    '''
    Args:
      grads_and_vars: gradients to apply and compute running average variance
      extra_grads_and_vars: gradients to apply (not used to compute average variance)
    '''
    # Variance summaries
    first_moment = U.vectorize(grads_and_vars, skip_none=True)
    second_moment = tf.square(first_moment)
    self.maintain_ema_ops.append(self.ema.apply([first_moment, second_moment]))

    # Add baseline losses
    if len(self.baseline_loss) > 0:
      mean_baseline_loss = tf.reduce_mean(tf.add_n(self.baseline_loss))
      extra_grads_and_vars += self.optimizer_class.compute_gradients(
          mean_baseline_loss,
          var_list=tf.get_collection('BASELINE'))

    # Ensure that all required tensors are computed before updates are executed
    extra_optimizer = tf.train.AdamOptimizer(
        learning_rate=10*self.hparams.learning_rate,
        beta2=self.hparams.beta2)
    with tf.control_dependencies(
        [tf.group(*[g for g, _ in (grads_and_vars + extra_grads_and_vars) if g is not None])]):

      # Filter out the P_COLLECTION variables if we're in eval mode
      if self.eval_mode:
        grads_and_vars = [(g, v) for g, v in grads_and_vars
                          if v not in tf.get_collection(P_COLLECTION)]

      train_op = self.optimizer_class.apply_gradients(grads_and_vars,
                                                      global_step=self.global_step)

      if len(extra_grads_and_vars) > 0:
        extra_train_op = extra_optimizer.apply_gradients(extra_grads_and_vars)
      else:
        extra_train_op = tf.no_op()

      self.optimizer = tf.group(train_op, extra_train_op, *self.maintain_ema_ops)

    # per parameter variance
    variance_estimator = (self.ema.average(second_moment) -
        tf.square(self.ema.average(first_moment)))
    self.grad_variance = tf.reduce_mean(variance_estimator)