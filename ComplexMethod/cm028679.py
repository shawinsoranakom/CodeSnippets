def run(self) -> Tuple[tf_keras.Model, Mapping[str, Any]]:
    """Run experiments by mode.

    Returns:
      A 2-tuple of (model, eval_logs).
        model: `tf_keras.Model` instance.
        eval_logs: returns eval metrics logs when run_post_eval is set to True,
          otherwise, returns {}.
    """
    mode = self._mode
    params = self.params
    logging.info('Starts to execute mode: %s', mode)
    with self.strategy.scope():
      if mode == 'train' or mode == 'train_and_post_eval':
        self.controller.train(steps=params.trainer.train_steps)
      elif mode == 'train_and_eval':
        self.controller.train_and_evaluate(
            train_steps=params.trainer.train_steps,
            eval_steps=params.trainer.validation_steps,
            eval_interval=params.trainer.validation_interval)
      elif mode == 'eval':
        self.controller.evaluate(steps=params.trainer.validation_steps)
      elif mode == 'continuous_eval':

        def timeout_fn():
          if self.trainer.global_step.numpy() >= params.trainer.train_steps:
            return True
          return False

        self.controller.evaluate_continuously(
            steps=params.trainer.validation_steps,
            timeout=params.trainer.continuous_eval_timeout,
            timeout_fn=timeout_fn)
      else:
        raise NotImplementedError('The mode is not implemented: %s' % mode)

    num_params = train_utils.try_count_params(self.trainer.model)
    if num_params is not None:
      logging.info('Number of trainable params in model: %f Millions.',
                   num_params / 10.**6)

    flops = train_utils.try_count_flops(self.trainer.model)
    if flops is not None:
      logging.info('FLOPs (multi-adds) in model: %f Billions.',
                   flops / 10.**9 / 2)

    if self._run_post_eval or mode == 'train_and_post_eval':
      with self.strategy.scope():
        return self.trainer.model, self.controller.evaluate(  # pytype: disable=bad-return-type  # always-use-property-annotation
            steps=params.trainer.validation_steps)
    else:
      return self.trainer.model, {}