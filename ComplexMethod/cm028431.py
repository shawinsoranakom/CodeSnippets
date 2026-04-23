def run_executor(params,
                 mode,
                 checkpoint_path=None,
                 train_input_fn=None,
                 eval_input_fn=None,
                 callbacks=None,
                 prebuilt_strategy=None):
  """Runs the object detection model on distribution strategy defined by the user."""

  if params.architecture.use_bfloat16:
    tf.compat.v2.keras.mixed_precision.set_global_policy('mixed_bfloat16')

  model_builder = model_factory.model_generator(params)

  if prebuilt_strategy is not None:
    strategy = prebuilt_strategy
  else:
    strategy_config = params.strategy_config
    distribute_utils.configure_cluster(strategy_config.worker_hosts,
                                       strategy_config.task_index)
    strategy = distribute_utils.get_distribution_strategy(
        distribution_strategy=params.strategy_type,
        num_gpus=strategy_config.num_gpus,
        all_reduce_alg=strategy_config.all_reduce_alg,
        num_packs=strategy_config.num_packs,
        tpu_address=strategy_config.tpu)

  num_workers = int(strategy.num_replicas_in_sync + 7) // 8
  is_multi_host = (int(num_workers) >= 2)

  if mode == 'train':

    def _model_fn(params):
      return model_builder.build_model(params, mode=ModeKeys.TRAIN)

    logging.info(
        'Train num_replicas_in_sync %d num_workers %d is_multi_host %s',
        strategy.num_replicas_in_sync, num_workers, is_multi_host)

    dist_executor = DetectionDistributedExecutor(
        strategy=strategy,
        params=params,
        model_fn=_model_fn,
        loss_fn=model_builder.build_loss_fn,
        is_multi_host=is_multi_host,
        predict_post_process_fn=model_builder.post_processing,
        trainable_variables_filter=model_builder
        .make_filter_trainable_variables_fn())

    if is_multi_host:
      train_input_fn = functools.partial(
          train_input_fn,
          batch_size=params.train.batch_size // strategy.num_replicas_in_sync)

    return dist_executor.train(
        train_input_fn=train_input_fn,
        model_dir=params.model_dir,
        iterations_per_loop=params.train.iterations_per_loop,
        total_steps=params.train.total_steps,
        init_checkpoint=model_builder.make_restore_checkpoint_fn(),
        custom_callbacks=callbacks,
        save_config=True)
  elif mode == 'eval' or mode == 'eval_once':

    def _model_fn(params):
      return model_builder.build_model(params, mode=ModeKeys.PREDICT_WITH_GT)

    logging.info('Eval num_replicas_in_sync %d num_workers %d is_multi_host %s',
                 strategy.num_replicas_in_sync, num_workers, is_multi_host)

    if is_multi_host:
      eval_input_fn = functools.partial(
          eval_input_fn,
          batch_size=params.eval.batch_size // strategy.num_replicas_in_sync)

    dist_executor = DetectionDistributedExecutor(
        strategy=strategy,
        params=params,
        model_fn=_model_fn,
        loss_fn=model_builder.build_loss_fn,
        is_multi_host=is_multi_host,
        predict_post_process_fn=model_builder.post_processing,
        trainable_variables_filter=model_builder
        .make_filter_trainable_variables_fn())

    if mode == 'eval':
      results = dist_executor.evaluate_from_model_dir(
          model_dir=params.model_dir,
          eval_input_fn=eval_input_fn,
          eval_metric_fn=model_builder.eval_metrics,
          eval_timeout=params.eval.eval_timeout,
          min_eval_interval=params.eval.min_eval_interval,
          total_steps=params.train.total_steps)
    else:
      # Run evaluation once for a single checkpoint.
      if not checkpoint_path:
        raise ValueError('checkpoint_path cannot be empty.')
      if tf.io.gfile.isdir(checkpoint_path):
        checkpoint_path = tf.train.latest_checkpoint(checkpoint_path)
      summary_writer = executor.SummaryWriter(params.model_dir, 'eval')
      results, _ = dist_executor.evaluate_checkpoint(
          checkpoint_path=checkpoint_path,
          eval_input_fn=eval_input_fn,
          eval_metric_fn=model_builder.eval_metrics,
          summary_writer=summary_writer)
    for k, v in results.items():
      logging.info('Final eval metric %s: %f', k, v)
    return results
  else:
    raise ValueError('Mode not found: %s.' % mode)