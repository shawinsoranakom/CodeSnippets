def run_ncf(_):
  """Run NCF training and eval with Keras."""

  keras_utils.set_session_config(enable_xla=FLAGS.enable_xla)

  if FLAGS.seed is not None:
    print("Setting tf seed")
    tf.random.set_seed(FLAGS.seed)

  model_helpers.apply_clean(FLAGS)

  if FLAGS.dtype == "fp16" and FLAGS.fp16_implementation == "keras":
    tf_keras.mixed_precision.set_global_policy("mixed_float16")

  strategy = distribute_utils.get_distribution_strategy(
      distribution_strategy=FLAGS.distribution_strategy,
      num_gpus=FLAGS.num_gpus,
      tpu_address=FLAGS.tpu)

  params = ncf_common.parse_flags(FLAGS)
  params["distribute_strategy"] = strategy
  params["use_tpu"] = (FLAGS.distribution_strategy == "tpu")

  if params["use_tpu"] and not params["keras_use_ctl"]:
    logging.error("Custom training loop must be used when using TPUStrategy.")
    return

  batch_size = params["batch_size"]
  time_callback = keras_utils.TimeHistory(batch_size, FLAGS.log_steps)
  callbacks = [time_callback]

  producer, input_meta_data = None, None
  generate_input_online = params["train_dataset_path"] is None

  if generate_input_online:
    # Start data producing thread.
    num_users, num_items, _, _, producer = ncf_common.get_inputs(params)
    producer.start()
    per_epoch_callback = IncrementEpochCallback(producer)
    callbacks.append(per_epoch_callback)
  else:
    assert params["eval_dataset_path"] and params["input_meta_data_path"]
    with tf.io.gfile.GFile(params["input_meta_data_path"], "rb") as reader:
      input_meta_data = json.loads(reader.read().decode("utf-8"))
      num_users = input_meta_data["num_users"]
      num_items = input_meta_data["num_items"]

  params["num_users"], params["num_items"] = num_users, num_items

  if FLAGS.early_stopping:
    early_stopping_callback = CustomEarlyStopping(
        "val_HR_METRIC", desired_value=FLAGS.hr_threshold)
    callbacks.append(early_stopping_callback)

  (train_input_dataset, eval_input_dataset, num_train_steps,
   num_eval_steps) = ncf_input_pipeline.create_ncf_input_data(
       params, producer, input_meta_data, strategy)
  steps_per_epoch = None if generate_input_online else num_train_steps

  with distribute_utils.get_strategy_scope(strategy):
    keras_model = _get_keras_model(params)
    optimizer = tf_keras.optimizers.Adam(
        learning_rate=params["learning_rate"],
        beta_1=params["beta1"],
        beta_2=params["beta2"],
        epsilon=params["epsilon"])
    if FLAGS.fp16_implementation == "graph_rewrite":
      optimizer = \
        tf.compat.v1.train.experimental.enable_mixed_precision_graph_rewrite(
            optimizer,
            loss_scale=flags_core.get_loss_scale(FLAGS,
                                                 default_for_fp16="dynamic"))
    elif FLAGS.dtype == "fp16":
      loss_scale = flags_core.get_loss_scale(FLAGS, default_for_fp16="dynamic")
      # Note Model.compile automatically wraps the optimizer with a
      # LossScaleOptimizer using dynamic loss scaling. We explicitly wrap it
      # here for the case where a custom training loop or fixed loss scale is
      # used.
      if loss_scale == "dynamic":
        optimizer = tf_keras.mixed_precision.LossScaleOptimizer(optimizer)
      else:
        optimizer = tf_keras.mixed_precision.LossScaleOptimizer(
            optimizer, dynamic=False, initial_scale=loss_scale)

    if params["keras_use_ctl"]:
      train_loss, eval_results = run_ncf_custom_training(
          params,
          strategy,
          keras_model,
          optimizer,
          callbacks,
          train_input_dataset,
          eval_input_dataset,
          num_train_steps,
          num_eval_steps,
          generate_input_online=generate_input_online)
    else:
      keras_model.compile(optimizer=optimizer, run_eagerly=FLAGS.run_eagerly)

      if not FLAGS.ml_perf:
        # Create Tensorboard summary and checkpoint callbacks.
        summary_dir = os.path.join(FLAGS.model_dir, "summaries")
        summary_callback = tf_keras.callbacks.TensorBoard(
            summary_dir, profile_batch=0)
        checkpoint_path = os.path.join(FLAGS.model_dir, "checkpoint")
        checkpoint_callback = tf_keras.callbacks.ModelCheckpoint(
            checkpoint_path, save_weights_only=True)

        callbacks += [summary_callback, checkpoint_callback]

      history = keras_model.fit(
          train_input_dataset,
          epochs=FLAGS.train_epochs,
          steps_per_epoch=steps_per_epoch,
          callbacks=callbacks,
          validation_data=eval_input_dataset,
          validation_steps=num_eval_steps,
          verbose=2)

      logging.info("Training done. Start evaluating")

      eval_loss_and_metrics = keras_model.evaluate(
          eval_input_dataset, steps=num_eval_steps, verbose=2)

      logging.info("Keras evaluation is done.")

      # Keras evaluate() API returns scalar loss and metric values from
      # evaluation as a list. Here, the returned list would contain
      # [evaluation loss, hr sum, hr count].
      eval_hit_rate = eval_loss_and_metrics[1] / eval_loss_and_metrics[2]

      # Format evaluation result into [eval loss, eval hit accuracy].
      eval_results = [eval_loss_and_metrics[0], eval_hit_rate]

      if history and history.history:
        train_history = history.history
        train_loss = train_history["loss"][-1]

  stats = build_stats(train_loss, eval_results, time_callback)
  return stats