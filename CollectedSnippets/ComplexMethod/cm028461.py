def build_stats(history, eval_output, callbacks):
  """Normalizes and returns dictionary of stats.

  Args:
    history: Results of the training step. Supports both categorical_accuracy
      and sparse_categorical_accuracy.
    eval_output: Output of the eval step. Assumes first value is eval_loss and
      second value is accuracy_top_1.
    callbacks: a list of callbacks which might include a time history callback
      used during keras.fit.

  Returns:
    Dictionary of normalized results.
  """
  stats = {}
  if eval_output:
    stats['accuracy_top_1'] = float(eval_output[1])
    stats['eval_loss'] = float(eval_output[0])
  if history and history.history:
    train_hist = history.history
    # Gets final loss from training.
    stats['loss'] = float(train_hist['loss'][-1])
    # Gets top_1 training accuracy.
    if 'categorical_accuracy' in train_hist:
      stats[TRAIN_TOP_1] = float(train_hist['categorical_accuracy'][-1])
    elif 'sparse_categorical_accuracy' in train_hist:
      stats[TRAIN_TOP_1] = float(train_hist['sparse_categorical_accuracy'][-1])
    elif 'accuracy' in train_hist:
      stats[TRAIN_TOP_1] = float(train_hist['accuracy'][-1])

  if not callbacks:
    return stats

  # Look for the time history callback which was used during keras.fit
  for callback in callbacks:
    if isinstance(callback, keras_utils.TimeHistory):
      timestamp_log = callback.timestamp_log
      stats['step_timestamp_log'] = timestamp_log
      stats['train_finish_time'] = callback.train_finish_time
      if callback.epoch_runtime_log:
        stats['avg_exp_per_second'] = callback.average_examples_per_second

  return stats