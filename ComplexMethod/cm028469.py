def train(self):
    """Trains the model."""
    params = self.params
    flags_obj = self.flags_obj
    # Sets config options.
    keras_utils.set_session_config(enable_xla=flags_obj.enable_xla)

    _ensure_dir(flags_obj.model_dir)
    with distribute_utils.get_strategy_scope(self.distribution_strategy):
      model = transformer.create_model(params, is_train=True)
      opt = self._create_optimizer()

      current_step = 0
      checkpoint = tf.train.Checkpoint(model=model, optimizer=opt)
      latest_checkpoint = tf.train.latest_checkpoint(flags_obj.model_dir)
      if latest_checkpoint:
        checkpoint.restore(latest_checkpoint)
        logging.info("Loaded checkpoint %s", latest_checkpoint)
        current_step = opt.iterations.numpy()

      if params["use_ctl"]:
        train_loss_metric = tf_keras.metrics.Mean(
            "training_loss", dtype=tf.float32)
        if params["enable_tensorboard"]:
          summary_writer = tf.summary.create_file_writer(
              os.path.join(flags_obj.model_dir, "summary"))
        else:
          summary_writer = tf.summary.create_noop_writer()
        train_metrics = [train_loss_metric]
        if params["enable_metrics_in_training"]:
          train_metrics = train_metrics + model.metrics
      else:
        model.compile(opt)

    model.summary()

    if self.use_tpu:
      # Different from experimental_distribute_dataset,
      # distribute_datasets_from_function requires
      # per-replica/local batch size.
      params["batch_size"] /= self.distribution_strategy.num_replicas_in_sync
      train_ds = (
          self.distribution_strategy.distribute_datasets_from_function(
              lambda ctx: data_pipeline.train_input_fn(params, ctx)))
    else:
      train_ds = data_pipeline.train_input_fn(params)
      map_data_fn = data_pipeline.map_data_for_transformer_fn
      train_ds = train_ds.map(
          map_data_fn, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    if params["use_ctl"]:
      train_ds_iterator = iter(train_ds)

    callbacks = self._create_callbacks(flags_obj.model_dir, params)

    # Only TimeHistory callback is supported for CTL
    if params["use_ctl"]:
      callbacks = [cb for cb in callbacks
                   if isinstance(cb, keras_utils.TimeHistory)]

    @tf.function
    def train_steps(iterator, steps):
      """Training steps function for TPU runs.

      Args:
        iterator: The input iterator of the training dataset.
        steps: An integer, the number of training steps.

      Returns:
        A float, the loss value.
      """

      def _step_fn(inputs):
        """Per-replica step function."""
        inputs, targets = inputs
        with tf.GradientTape() as tape:
          logits = model([inputs, targets], training=True)
          loss = metrics.transformer_loss(logits, targets,
                                          params["label_smoothing"],
                                          params["vocab_size"])
          # Scales the loss, which results in using the average loss across all
          # of the replicas for backprop.
          scaled_loss = loss / self.distribution_strategy.num_replicas_in_sync

        # De-dupes variables due to keras tracking issues.
        tvars = list({id(v): v for v in model.trainable_variables}.values())
        grads = tape.gradient(scaled_loss, tvars)
        opt.apply_gradients(zip(grads, tvars))
        # For reporting, the metric takes the mean of losses.
        train_loss_metric.update_state(loss)

      for _ in tf.range(steps):
        train_loss_metric.reset_states()
        self.distribution_strategy.run(
            _step_fn, args=(next(iterator),))

    cased_score, uncased_score = None, None
    cased_score_history, uncased_score_history = [], []
    while current_step < flags_obj.train_steps:
      remaining_steps = flags_obj.train_steps - current_step
      train_steps_per_eval = (
          remaining_steps if remaining_steps < flags_obj.steps_between_evals
          else flags_obj.steps_between_evals)
      current_iteration = current_step // flags_obj.steps_between_evals

      logging.info(
          "Start train iteration at global step:{}".format(current_step))
      history = None
      if params["use_ctl"]:
        if not self.use_tpu:
          raise NotImplementedError(
              "Custom training loop on GPUs is not implemented.")

        # Runs training steps.
        with summary_writer.as_default():
          for cb in callbacks:
            cb.on_epoch_begin(current_iteration)
            cb.on_batch_begin(0)

          train_steps(
              train_ds_iterator,
              tf.convert_to_tensor(train_steps_per_eval, dtype=tf.int32))
          current_step += train_steps_per_eval
          train_loss = train_loss_metric.result().numpy().astype(float)
          logging.info("Train Step: %d/%d / loss = %s", current_step,
                       flags_obj.train_steps, train_loss)

          for cb in callbacks:
            cb.on_batch_end(train_steps_per_eval - 1)
            cb.on_epoch_end(current_iteration)

          if params["enable_tensorboard"]:
            for metric_obj in train_metrics:
              tf.summary.scalar(metric_obj.name, metric_obj.result(),
                                current_step)
              summary_writer.flush()

        for cb in callbacks:
          cb.on_train_end()

        if flags_obj.enable_checkpointing:
          # avoid check-pointing when running for benchmarking.
          checkpoint_name = checkpoint.save(
              os.path.join(flags_obj.model_dir,
                           "ctl_step_{}.ckpt".format(current_step)))
          logging.info("Saved checkpoint to %s", checkpoint_name)
      else:
        if self.use_tpu:
          raise NotImplementedError(
              "Keras model.fit on TPUs is not implemented.")
        history = model.fit(
            train_ds,
            initial_epoch=current_iteration,
            epochs=current_iteration + 1,
            steps_per_epoch=train_steps_per_eval,
            callbacks=callbacks,
            # If TimeHistory is enabled, progress bar would be messy. Increase
            # the verbose level to get rid of it.
            verbose=(2 if flags_obj.enable_time_history else 1))
        current_step += train_steps_per_eval
        logging.info("Train history: {}".format(history.history))

      logging.info("End train iteration at global step:{}".format(current_step))

      if (flags_obj.bleu_source and flags_obj.bleu_ref):
        uncased_score, cased_score = self.eval()
        cased_score_history.append([current_iteration + 1, cased_score])
        uncased_score_history.append([current_iteration + 1, uncased_score])

    stats = ({
        "loss": train_loss
    } if history is None else {})
    misc.update_stats(history, stats, callbacks)
    if uncased_score and cased_score:
      stats["bleu_uncased"] = uncased_score
      stats["bleu_cased"] = cased_score
      stats["bleu_uncased_history"] = uncased_score_history
      stats["bleu_cased_history"] = cased_score_history
    return stats