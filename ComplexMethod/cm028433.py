def train(
      self,
      train_input_fn: Callable[[params_dict.ParamsDict], tf.data.Dataset],
      eval_input_fn: Optional[Callable[[params_dict.ParamsDict],
                                       tf.data.Dataset]] = None,
      model_dir: Optional[Text] = None,
      total_steps: int = 1,
      iterations_per_loop: int = 1,
      train_metric_fn: Optional[Callable[[], Any]] = None,
      eval_metric_fn: Optional[Callable[[], Any]] = None,
      summary_writer_fn: Callable[[Text, Text], SummaryWriter] = SummaryWriter,
      init_checkpoint: Optional[Callable[[tf_keras.Model], Any]] = None,
      custom_callbacks: Optional[List[tf_keras.callbacks.Callback]] = None,
      continuous_eval: bool = False,
      save_config: bool = True):
    """Runs distributed training.

    Args:
      train_input_fn: (params: dict) -> tf.data.Dataset training data input
        function.
      eval_input_fn: (Optional) same type as train_input_fn. If not None, will
        trigger evaluating metric on eval data. If None, will not run the eval
        step.
      model_dir: the folder path for model checkpoints.
      total_steps: total training steps.
      iterations_per_loop: train steps per loop. After each loop, this job will
        update metrics like loss and save checkpoint.
      train_metric_fn: metric_fn for evaluation in train_step.
      eval_metric_fn: metric_fn for evaluation in test_step.
      summary_writer_fn: function to create summary writer.
      init_checkpoint: function to load checkpoint.
      custom_callbacks: A list of Keras Callbacks objects to run during
        training. More specifically, `on_batch_begin()`, `on_batch_end()`,
        methods are invoked during training.
      continuous_eval: If `True`, will continously run evaluation on every
        available checkpoints. If `False`, will do the evaluation once after the
        final step.
      save_config: bool. Whether to save params to model_dir.

    Returns:
      The training loss and eval metrics.
    """
    assert train_input_fn is not None
    if train_metric_fn and not callable(train_metric_fn):
      raise ValueError('if `train_metric_fn` is specified, '
                       'train_metric_fn must be a callable.')
    if eval_metric_fn and not callable(eval_metric_fn):
      raise ValueError('if `eval_metric_fn` is specified, '
                       'eval_metric_fn must be a callable.')
    train_metric_fn = train_metric_fn or _no_metric
    eval_metric_fn = eval_metric_fn or _no_metric

    if custom_callbacks and iterations_per_loop != 1:
      logging.warning(
          'It is sematically wrong to run callbacks when '
          'iterations_per_loop is not one (%s)', iterations_per_loop)

    custom_callbacks = custom_callbacks or []

    def _run_callbacks_on_batch_begin(batch):
      """Runs custom callbacks at the start of every step."""
      if not custom_callbacks:
        return
      for callback in custom_callbacks:
        if callback:
          callback.on_batch_begin(batch)

    def _run_callbacks_on_batch_end(batch):
      """Runs custom callbacks at the end of every step."""
      if not custom_callbacks:
        return
      for callback in custom_callbacks:
        if callback:
          callback.on_batch_end(batch)

    if save_config:
      self._save_config(model_dir)

    if FLAGS.save_checkpoint_freq:
      save_freq = FLAGS.save_checkpoint_freq
    else:
      save_freq = iterations_per_loop

    params = self._params
    strategy = self._strategy
    # To reduce unnecessary send/receive input pipeline operation, we place
    # input pipeline ops in worker task.
    train_iterator = self._get_input_iterator(train_input_fn, strategy)
    train_loss = None
    train_metric_result = None
    eval_metric_result = None
    tf_keras.backend.set_learning_phase(1)
    with strategy.scope():
      # To correctly place the model weights on accelerators,
      # model and optimizer should be created in scope.
      model = self.model_fn(params.as_dict())
      if not hasattr(model, 'optimizer'):
        raise ValueError('User should set optimizer attribute to model '
                         'inside `model_fn`.')
      optimizer = model.optimizer

      # Training loop starts here.
      checkpoint = tf.train.Checkpoint(model=model, optimizer=optimizer)
      latest_checkpoint_file = tf.train.latest_checkpoint(model_dir)
      initial_step = 0
      if latest_checkpoint_file:
        logging.info(
            'Checkpoint file %s found and restoring from '
            'checkpoint', latest_checkpoint_file)
        checkpoint.restore(latest_checkpoint_file)
        initial_step = optimizer.iterations.numpy()
        logging.info('Loading from checkpoint file completed. Init step %d',
                     initial_step)
      elif init_checkpoint:
        logging.info('Restoring from init checkpoint function')
        init_checkpoint(model)
        logging.info('Loading from init checkpoint file completed')

      current_step = optimizer.iterations.numpy()
      checkpoint_name = self.checkpoint_name

      eval_metric = eval_metric_fn()
      train_metric = train_metric_fn()
      train_summary_writer = summary_writer_fn(model_dir, 'eval_train')
      self.train_summary_writer = train_summary_writer.writer

      test_summary_writer = summary_writer_fn(model_dir, 'eval_test')
      self.eval_summary_writer = test_summary_writer.writer

    # Use training summary writer in TimeHistory if it's in use
    for cb in custom_callbacks:
      if isinstance(cb, keras_utils.TimeHistory):
        cb.summary_writer = self.train_summary_writer

    # Continue training loop.
    train_step = self._create_train_step(
        strategy=strategy,
        model=model,
        loss_fn=self.loss_fn(),
        optimizer=optimizer,
        metric=train_metric)
    test_step = None
    if eval_input_fn and eval_metric:
      self.global_train_step = model.optimizer.iterations
      test_step = self._create_test_step(strategy, model, metric=eval_metric)

    # Step-0 operations
    if current_step == 0 and not latest_checkpoint_file:
      _save_checkpoint(checkpoint, model_dir,
                       checkpoint_name.format(step=current_step))
    if test_step:
      eval_iterator = self._get_input_iterator(eval_input_fn, strategy)
      eval_metric_result = self._run_evaluation(test_step, current_step,
                                                eval_metric, eval_iterator)
      logging.info('Step: %s evalation metric = %s.', current_step,
                   eval_metric_result)
      test_summary_writer(metrics=eval_metric_result, step=optimizer.iterations)
      reset_states(eval_metric)

    logging.info('Training started')
    last_save_checkpoint_step = current_step
    while current_step < total_steps:

      num_steps = _steps_to_run(current_step, total_steps, iterations_per_loop)
      _run_callbacks_on_batch_begin(current_step)
      train_loss = train_step(train_iterator,
                              tf.convert_to_tensor(num_steps, dtype=tf.int32))
      current_step += num_steps

      train_loss = tf.nest.map_structure(lambda x: x.numpy().astype(float),
                                         train_loss)

      _run_callbacks_on_batch_end(current_step - 1)
      if not isinstance(train_loss, dict):
        train_loss = {'total_loss': train_loss}
      if np.isnan(train_loss['total_loss']):
        raise ValueError('total loss is NaN.')

      if train_metric:
        train_metric_result = metric_results(train_metric)
        train_metric_result.update(train_loss)
      else:
        train_metric_result = train_loss
      if callable(optimizer.lr):
        train_metric_result.update(
            {'learning_rate': optimizer.lr(current_step).numpy()})
      else:
        train_metric_result.update({'learning_rate': optimizer.lr.numpy()})
      logging.info('Train Step: %d/%d  / loss = %s / training metric = %s',
                   current_step, total_steps, train_loss, train_metric_result)

      train_summary_writer(
          metrics=train_metric_result, step=optimizer.iterations)

      # Saves model checkpoints and run validation steps at every
      # iterations_per_loop steps.
      # To avoid repeated model saving, we do not save after the last
      # step of training.
      if save_freq > 0 and current_step < total_steps and (
          current_step - last_save_checkpoint_step) >= save_freq:
        _save_checkpoint(checkpoint, model_dir,
                         checkpoint_name.format(step=current_step))
        last_save_checkpoint_step = current_step

      if continuous_eval and current_step < total_steps and test_step:
        eval_iterator = self._get_input_iterator(eval_input_fn, strategy)
        eval_metric_result = self._run_evaluation(test_step, current_step,
                                                  eval_metric, eval_iterator)
        logging.info('Step: %s evalation metric = %s.', current_step,
                     eval_metric_result)
        test_summary_writer(
            metrics=eval_metric_result, step=optimizer.iterations)

      # Re-initialize evaluation metric, except the last step.
      if eval_metric and current_step < total_steps:
        reset_states(eval_metric)
      if train_metric and current_step < total_steps:
        reset_states(train_metric)

    # Reaches the end of training and saves the last checkpoint.
    if last_save_checkpoint_step < total_steps:
      _save_checkpoint(checkpoint, model_dir,
                       checkpoint_name.format(step=current_step))

    if test_step:
      logging.info('Running final evaluation after training is complete.')
      eval_iterator = self._get_input_iterator(eval_input_fn, strategy)
      eval_metric_result = self._run_evaluation(test_step, current_step,
                                                eval_metric, eval_iterator)
      logging.info('Final evaluation metric = %s.', eval_metric_result)
      test_summary_writer(metrics=eval_metric_result, step=optimizer.iterations)

    self.train_summary_writer.close()
    self.eval_summary_writer.close()

    return train_metric_result, eval_metric_result