def train_loop(
    pipeline_config_path,
    model_dir,
    config_override=None,
    train_steps=None,
    use_tpu=False,
    save_final_config=False,
    checkpoint_every_n=1000,
    checkpoint_max_to_keep=7,
    record_summaries=True,
    performance_summary_exporter=None,
    num_steps_per_iteration=NUM_STEPS_PER_ITERATION,
    **kwargs):
  """Trains a model using eager + functions.

  This method:
    1. Processes the pipeline configs
    2. (Optionally) saves the as-run config
    3. Builds the model & optimizer
    4. Gets the training input data
    5. Loads a fine-tuning detection or classification checkpoint if requested
    6. Loops over the train data, executing distributed training steps inside
       tf.functions.
    7. Checkpoints the model every `checkpoint_every_n` training steps.
    8. Logs the training metrics as TensorBoard summaries.

  Args:
    pipeline_config_path: A path to a pipeline config file.
    model_dir:
      The directory to save checkpoints and summaries to.
    config_override: A pipeline_pb2.TrainEvalPipelineConfig text proto to
      override the config from `pipeline_config_path`.
    train_steps: Number of training steps. If None, the number of training steps
      is set from the `TrainConfig` proto.
    use_tpu: Boolean, whether training and evaluation should run on TPU.
    save_final_config: Whether to save final config (obtained after applying
      overrides) to `model_dir`.
    checkpoint_every_n:
      Checkpoint every n training steps.
    checkpoint_max_to_keep:
      int, the number of most recent checkpoints to keep in the model directory.
    record_summaries: Boolean, whether or not to record summaries defined by
      the model or the training pipeline. This does not impact the summaries
      of the loss values which are always recorded. Examples of summaries
      that are controlled by this flag include:
        - Image summaries of training images.
        - Intermediate tensors which maybe logged by meta architectures.
    performance_summary_exporter: function for exporting performance metrics.
    num_steps_per_iteration: int, The number of training steps to perform
      in each iteration.
    **kwargs: Additional keyword arguments for configuration override.
  """
  ## Parse the configs
  get_configs_from_pipeline_file = MODEL_BUILD_UTIL_MAP[
      'get_configs_from_pipeline_file']
  merge_external_params_with_configs = MODEL_BUILD_UTIL_MAP[
      'merge_external_params_with_configs']
  create_pipeline_proto_from_configs = MODEL_BUILD_UTIL_MAP[
      'create_pipeline_proto_from_configs']
  steps_per_sec_list = []

  configs = get_configs_from_pipeline_file(
      pipeline_config_path, config_override=config_override)
  kwargs.update({
      'train_steps': train_steps,
      'use_bfloat16': configs['train_config'].use_bfloat16 and use_tpu
  })
  configs = merge_external_params_with_configs(
      configs, None, kwargs_dict=kwargs)
  model_config = configs['model']
  train_config = configs['train_config']
  train_input_config = configs['train_input_config']

  unpad_groundtruth_tensors = train_config.unpad_groundtruth_tensors
  add_regularization_loss = train_config.add_regularization_loss
  clip_gradients_value = None
  if train_config.gradient_clipping_by_norm > 0:
    clip_gradients_value = train_config.gradient_clipping_by_norm

  # update train_steps from config but only when non-zero value is provided
  if train_steps is None and train_config.num_steps != 0:
    train_steps = train_config.num_steps

  if kwargs['use_bfloat16']:
    tf.compat.v2.keras.mixed_precision.set_global_policy('mixed_bfloat16')

  if train_config.load_all_detection_checkpoint_vars:
    raise ValueError('train_pb2.load_all_detection_checkpoint_vars '
                     'unsupported in TF2')

  config_util.update_fine_tune_checkpoint_type(train_config)
  fine_tune_checkpoint_type = train_config.fine_tune_checkpoint_type
  fine_tune_checkpoint_version = train_config.fine_tune_checkpoint_version

  # Write the as-run pipeline config to disk.
  if save_final_config:
    tf.logging.info('Saving pipeline config file to directory %s', model_dir)
    pipeline_config_final = create_pipeline_proto_from_configs(configs)
    config_util.save_pipeline_config(pipeline_config_final, model_dir)

  # Build the model, optimizer, and training input
  strategy = tf.compat.v2.distribute.get_strategy()
  with strategy.scope():
    detection_model = MODEL_BUILD_UTIL_MAP['detection_model_fn_base'](
        model_config=model_config, is_training=True,
        add_summaries=record_summaries)

    def train_dataset_fn(input_context):
      """Callable to create train input."""
      # Create the inputs.
      train_input = inputs.train_input(
          train_config=train_config,
          train_input_config=train_input_config,
          model_config=model_config,
          model=detection_model,
          input_context=input_context)
      train_input = train_input.repeat()
      return train_input

    train_input = strategy.experimental_distribute_datasets_from_function(
        train_dataset_fn)


    global_step = tf.Variable(
        0, trainable=False, dtype=tf.compat.v2.dtypes.int64, name='global_step',
        aggregation=tf.compat.v2.VariableAggregation.ONLY_FIRST_REPLICA)
    optimizer, (learning_rate,) = optimizer_builder.build(
        train_config.optimizer, global_step=global_step)

    # We run the detection_model on dummy inputs in order to ensure that the
    # model and all its variables have been properly constructed. Specifically,
    # this is currently necessary prior to (potentially) creating shadow copies
    # of the model variables for the EMA optimizer.
    if train_config.optimizer.use_moving_average:
      _ensure_model_is_built(detection_model, train_input,
                             unpad_groundtruth_tensors)
      optimizer.shadow_copy(detection_model)

    if callable(learning_rate):
      learning_rate_fn = learning_rate
    else:
      learning_rate_fn = lambda: learning_rate

  ## Train the model
  # Get the appropriate filepath (temporary or not) based on whether the worker
  # is the chief.
  summary_writer_filepath = get_filepath(strategy,
                                         os.path.join(model_dir, 'train'))

  summary_writer = tf.compat.v2.summary.create_file_writer(
      summary_writer_filepath)

  with summary_writer.as_default():
    with strategy.scope():
      with tf.compat.v2.summary.record_if(
          lambda: global_step % num_steps_per_iteration == 0):
        # Load a fine-tuning checkpoint.
        if train_config.fine_tune_checkpoint:
          variables_helper.ensure_checkpoint_supported(
              train_config.fine_tune_checkpoint, fine_tune_checkpoint_type,
              model_dir)
          load_fine_tune_checkpoint(
              detection_model, train_config.fine_tune_checkpoint,
              fine_tune_checkpoint_type, fine_tune_checkpoint_version,
              train_config.run_fine_tune_checkpoint_dummy_computation,
              train_input, unpad_groundtruth_tensors)

        ckpt = tf.compat.v2.train.Checkpoint(
            step=global_step, model=detection_model, optimizer=optimizer)

        manager_dir = get_filepath(strategy, model_dir)
        if not strategy.extended.should_checkpoint:
          checkpoint_max_to_keep = 1
        manager = tf.compat.v2.train.CheckpointManager(
            ckpt, manager_dir, max_to_keep=checkpoint_max_to_keep)

        # We use the following instead of manager.latest_checkpoint because
        # manager_dir does not point to the model directory when we are running
        # in a worker.
        latest_checkpoint = tf.train.latest_checkpoint(model_dir)
        ckpt.restore(latest_checkpoint)

        def train_step_fn(features, labels):
          """Single train step."""

          if record_summaries:
            tf.compat.v2.summary.image(
                name='train_input_images',
                step=global_step,
                data=features[fields.InputDataFields.image],
                max_outputs=3)
          losses_dict = eager_train_step(
              detection_model,
              features,
              labels,
              unpad_groundtruth_tensors,
              optimizer,
              training_step=global_step,
              add_regularization_loss=add_regularization_loss,
              clip_gradients_value=clip_gradients_value,
              num_replicas=strategy.num_replicas_in_sync)
          global_step.assign_add(1)
          return losses_dict

        def _sample_and_train(strategy, train_step_fn, data_iterator):
          features, labels = data_iterator.next()
          if hasattr(tf.distribute.Strategy, 'run'):
            per_replica_losses_dict = strategy.run(
                train_step_fn, args=(features, labels))
          else:
            per_replica_losses_dict = (
                strategy.experimental_run_v2(
                    train_step_fn, args=(features, labels)))

          return reduce_dict(
              strategy, per_replica_losses_dict, tf.distribute.ReduceOp.SUM)

        @tf.function
        def _dist_train_step(data_iterator):
          """A distributed train step."""

          if num_steps_per_iteration > 1:
            for _ in tf.range(num_steps_per_iteration - 1):
              # Following suggestion on yaqs/5402607292645376
              with tf.name_scope(''):
                _sample_and_train(strategy, train_step_fn, data_iterator)

          return _sample_and_train(strategy, train_step_fn, data_iterator)

        train_input_iter = iter(train_input)

        if int(global_step.value()) == 0:
          manager.save()

        checkpointed_step = int(global_step.value())
        logged_step = global_step.value()

        last_step_time = time.time()
        for _ in range(global_step.value(), train_steps,
                       num_steps_per_iteration):

          losses_dict = _dist_train_step(train_input_iter)

          time_taken = time.time() - last_step_time
          last_step_time = time.time()
          steps_per_sec = num_steps_per_iteration * 1.0 / time_taken

          tf.compat.v2.summary.scalar(
              'steps_per_sec', steps_per_sec, step=global_step)

          steps_per_sec_list.append(steps_per_sec)

          logged_dict = losses_dict.copy()
          logged_dict['learning_rate'] = learning_rate_fn()

          for key, val in logged_dict.items():
            tf.compat.v2.summary.scalar(key, val, step=global_step)

          if global_step.value() - logged_step >= LOG_EVERY:
            logged_dict_np = {name: value.numpy() for name, value in
                              logged_dict.items()}
            tf.logging.info(
                'Step {} per-step time {:.3f}s'.format(
                    global_step.value(), time_taken / num_steps_per_iteration))
            tf.logging.info(pprint.pformat(logged_dict_np, width=40))
            logged_step = global_step.value()

          if ((int(global_step.value()) - checkpointed_step) >=
              checkpoint_every_n):
            manager.save()
            checkpointed_step = int(global_step.value())

  # Remove the checkpoint directories of the non-chief workers that
  # MultiWorkerMirroredStrategy forces us to save during sync distributed
  # training.
  clean_temporary_directories(strategy, manager_dir)
  clean_temporary_directories(strategy, summary_writer_filepath)
  # TODO(pkanwar): add accuracy metrics.
  if performance_summary_exporter is not None:
    metrics = {
        'steps_per_sec': np.mean(steps_per_sec_list),
        'steps_per_sec_p50': np.median(steps_per_sec_list),
        'steps_per_sec_max': max(steps_per_sec_list),
        'last_batch_loss': float(losses_dict['Loss/total_loss'])
    }
    mixed_precision = 'bf16' if kwargs['use_bfloat16'] else 'fp32'
    performance_summary_exporter(metrics, mixed_precision)