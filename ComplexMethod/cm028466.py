def run_keras_compile_fit(model_dir,
                          strategy,
                          model_fn,
                          train_input_fn,
                          eval_input_fn,
                          loss_fn,
                          metric_fn,
                          init_checkpoint,
                          epochs,
                          steps_per_epoch,
                          steps_per_loop,
                          eval_steps,
                          training_callbacks=True,
                          custom_callbacks=None):
  """Runs BERT classifier model using Keras compile/fit API."""

  with strategy.scope():
    training_dataset = train_input_fn()
    evaluation_dataset = eval_input_fn() if eval_input_fn else None
    bert_model, sub_model = model_fn()
    optimizer = bert_model.optimizer

    if init_checkpoint:
      checkpoint = tf.train.Checkpoint(model=sub_model, encoder=sub_model)
      checkpoint.read(init_checkpoint).assert_existing_objects_matched()

    if not isinstance(metric_fn, (list, tuple)):
      metric_fn = [metric_fn]
    bert_model.compile(
        optimizer=optimizer,
        loss=loss_fn,
        metrics=[fn() for fn in metric_fn],
        steps_per_execution=steps_per_loop)

    summary_dir = os.path.join(model_dir, 'summaries')
    summary_callback = tf_keras.callbacks.TensorBoard(summary_dir)
    checkpoint = tf.train.Checkpoint(model=bert_model, optimizer=optimizer)
    checkpoint_manager = tf.train.CheckpointManager(
        checkpoint,
        directory=model_dir,
        max_to_keep=None,
        step_counter=optimizer.iterations,
        checkpoint_interval=0)
    checkpoint_callback = keras_utils.SimpleCheckpoint(checkpoint_manager)

    if training_callbacks:
      if custom_callbacks is not None:
        custom_callbacks += [summary_callback, checkpoint_callback]
      else:
        custom_callbacks = [summary_callback, checkpoint_callback]

    history = bert_model.fit(
        x=training_dataset,
        validation_data=evaluation_dataset,
        steps_per_epoch=steps_per_epoch,
        epochs=epochs,
        validation_steps=eval_steps,
        callbacks=custom_callbacks)
    stats = {'total_training_steps': steps_per_epoch * epochs}
    if 'loss' in history.history:
      stats['train_loss'] = history.history['loss'][-1]
    if 'val_accuracy' in history.history:
      stats['eval_metrics'] = history.history['val_accuracy'][-1]
    return bert_model, stats