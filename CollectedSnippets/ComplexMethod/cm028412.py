def main(_) -> None:
  """Train and evaluate the Ranking model."""
  params = train_utils.parse_configuration(FLAGS)
  mode = FLAGS.mode
  model_dir = FLAGS.model_dir
  if 'train' in FLAGS.mode:
    # Pure eval modes do not output yaml files. Otherwise continuous eval job
    # may race against the train job for writing the same file.
    train_utils.serialize_config(params, model_dir)

  if FLAGS.seed is not None:
    logging.info('Setting tf seed.')
    tf.random.set_seed(FLAGS.seed)

  task = RankingTask(
      params=params.task,
      trainer_config=params.trainer,
      logging_dir=model_dir,
      steps_per_execution=params.trainer.steps_per_loop,
      name='RankingTask')

  enable_tensorboard = params.trainer.callbacks.enable_tensorboard

  strategy = distribute_utils.get_distribution_strategy(
      distribution_strategy=params.runtime.distribution_strategy,
      all_reduce_alg=params.runtime.all_reduce_alg,
      num_gpus=params.runtime.num_gpus,
      tpu_address=params.runtime.tpu)

  with strategy.scope():
    model = task.build_model()

  def get_dataset_fn(params):
    return lambda input_context: task.build_inputs(params, input_context)

  train_dataset = None
  if 'train' in mode:
    train_dataset = strategy.distribute_datasets_from_function(
        get_dataset_fn(params.task.train_data),
        options=tf.distribute.InputOptions(experimental_fetch_to_device=False))

  validation_dataset = None
  if 'eval' in mode:
    validation_dataset = strategy.distribute_datasets_from_function(
        get_dataset_fn(params.task.validation_data),
        options=tf.distribute.InputOptions(experimental_fetch_to_device=False))

  if params.trainer.use_orbit:
    with strategy.scope():
      checkpoint_exporter = train_utils.maybe_create_best_ckpt_exporter(
          params, model_dir)
      trainer = RankingTrainer(
          config=params,
          task=task,
          model=model,
          optimizer=model.optimizer,
          train='train' in mode,
          evaluate='eval' in mode,
          train_dataset=train_dataset,
          validation_dataset=validation_dataset,
          checkpoint_exporter=checkpoint_exporter)

    train_lib.run_experiment(
        distribution_strategy=strategy,
        task=task,
        mode=mode,
        params=params,
        model_dir=model_dir,
        trainer=trainer)

  else:  # Compile/fit
    checkpoint = tf.train.Checkpoint(model=model, optimizer=model.optimizer)

    latest_checkpoint = tf.train.latest_checkpoint(model_dir)
    if latest_checkpoint:
      checkpoint.restore(latest_checkpoint)
      logging.info('Loaded checkpoint %s', latest_checkpoint)

    checkpoint_manager = tf.train.CheckpointManager(
        checkpoint,
        directory=model_dir,
        max_to_keep=params.trainer.max_to_keep,
        step_counter=model.optimizer.iterations,
        checkpoint_interval=params.trainer.checkpoint_interval)
    checkpoint_callback = keras_utils.SimpleCheckpoint(checkpoint_manager)

    time_callback = keras_utils.TimeHistory(
        params.task.train_data.global_batch_size,
        params.trainer.time_history.log_steps,
        logdir=model_dir if enable_tensorboard else None)
    callbacks = [checkpoint_callback, time_callback]

    if enable_tensorboard:
      tensorboard_callback = tf_keras.callbacks.TensorBoard(
          log_dir=model_dir,
          update_freq=min(1000, params.trainer.validation_interval),
          profile_batch=FLAGS.profile_steps)
      callbacks.append(tensorboard_callback)

    num_epochs = (params.trainer.train_steps //
                  params.trainer.validation_interval)
    current_step = model.optimizer.iterations.numpy()
    initial_epoch = current_step // params.trainer.validation_interval

    eval_steps = params.trainer.validation_steps if 'eval' in mode else None

    if mode in ['train', 'train_and_eval']:
      logging.info('Training started')
      history = model.fit(
          train_dataset,
          initial_epoch=initial_epoch,
          epochs=num_epochs,
          steps_per_epoch=params.trainer.validation_interval,
          validation_data=validation_dataset,
          validation_steps=eval_steps,
          callbacks=callbacks,
      )
      model.summary()
      logging.info('Train history: %s', history.history)
    elif mode == 'eval':
      logging.info('Evaluation started')
      validation_output = model.evaluate(validation_dataset, steps=eval_steps)
      logging.info('Evaluation output: %s', validation_output)
    else:
      raise NotImplementedError('The mode is not implemented: %s' % mode)