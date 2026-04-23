def train_and_eval(
    params: base_configs.ExperimentConfig,
    strategy_override: tf.distribute.Strategy) -> Mapping[str, Any]:
  """Runs the train and eval path using compile/fit."""
  logging.info('Running train and eval.')

  distribute_utils.configure_cluster(params.runtime.worker_hosts,
                                     params.runtime.task_index)

  # Note: for TPUs, strategy and scope should be created before the dataset
  strategy = strategy_override or distribute_utils.get_distribution_strategy(
      distribution_strategy=params.runtime.distribution_strategy,
      all_reduce_alg=params.runtime.all_reduce_alg,
      num_gpus=params.runtime.num_gpus,
      tpu_address=params.runtime.tpu)

  strategy_scope = distribute_utils.get_strategy_scope(strategy)

  logging.info('Detected %d devices.',
               strategy.num_replicas_in_sync if strategy else 1)

  label_smoothing = params.model.loss.label_smoothing
  one_hot = label_smoothing and label_smoothing > 0

  builders = _get_dataset_builders(params, strategy, one_hot)
  datasets = [
      builder.build(strategy) if builder else None for builder in builders
  ]

  # Unpack datasets and builders based on train/val/test splits
  train_builder, validation_builder = builders  # pylint: disable=unbalanced-tuple-unpacking
  train_dataset, validation_dataset = datasets

  train_epochs = params.train.epochs
  train_steps = params.train.steps or train_builder.num_steps
  validation_steps = params.evaluation.steps or validation_builder.num_steps

  initialize(params, train_builder)

  logging.info('Global batch size: %d', train_builder.global_batch_size)

  with strategy_scope:
    model_params = params.model.model_params.as_dict()
    model = get_models()[params.model.name](**model_params)
    learning_rate = optimizer_factory.build_learning_rate(
        params=params.model.learning_rate,
        batch_size=train_builder.global_batch_size,
        train_epochs=train_epochs,
        train_steps=train_steps)
    optimizer = optimizer_factory.build_optimizer(
        optimizer_name=params.model.optimizer.name,
        base_learning_rate=learning_rate,
        params=params.model.optimizer.as_dict(),
        model=model)
    optimizer = performance.configure_optimizer(
        optimizer,
        use_float16=train_builder.dtype == 'float16',
        loss_scale=get_loss_scale(params))

    metrics_map = _get_metrics(one_hot)
    metrics = [metrics_map[metric] for metric in params.train.metrics]
    steps_per_loop = train_steps if params.train.set_epoch_loop else 1

    if one_hot:
      loss_obj = tf_keras.losses.CategoricalCrossentropy(
          label_smoothing=params.model.loss.label_smoothing)
    else:
      loss_obj = tf_keras.losses.SparseCategoricalCrossentropy()
    model.compile(
        optimizer=optimizer,
        loss=loss_obj,
        metrics=metrics,
        steps_per_execution=steps_per_loop)

    initial_epoch = 0
    if params.train.resume_checkpoint:
      initial_epoch = resume_from_checkpoint(
          model=model, model_dir=params.model_dir, train_steps=train_steps)

    callbacks = custom_callbacks.get_callbacks(
        model_checkpoint=params.train.callbacks.enable_checkpoint_and_export,
        include_tensorboard=params.train.callbacks.enable_tensorboard,
        time_history=params.train.callbacks.enable_time_history,
        track_lr=params.train.tensorboard.track_lr,
        write_model_weights=params.train.tensorboard.write_model_weights,
        initial_step=initial_epoch * train_steps,
        batch_size=train_builder.global_batch_size,
        log_steps=params.train.time_history.log_steps,
        model_dir=params.model_dir,
        backup_and_restore=params.train.callbacks.enable_backup_and_restore)

  serialize_config(params=params, model_dir=params.model_dir)

  if params.evaluation.skip_eval:
    validation_kwargs = {}
  else:
    validation_kwargs = {
        'validation_data': validation_dataset,
        'validation_steps': validation_steps,
        'validation_freq': params.evaluation.epochs_between_evals,
    }

  history = model.fit(
      train_dataset,
      epochs=train_epochs,
      steps_per_epoch=train_steps,
      initial_epoch=initial_epoch,
      callbacks=callbacks,
      verbose=2,
      **validation_kwargs)

  validation_output = None
  if not params.evaluation.skip_eval:
    validation_output = model.evaluate(
        validation_dataset, steps=validation_steps, verbose=2)

  # TODO(dankondratyuk): eval and save final test accuracy
  stats = common.build_stats(history, validation_output, callbacks)
  return stats