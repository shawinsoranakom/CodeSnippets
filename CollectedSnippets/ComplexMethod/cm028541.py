def continuous_eval(strategy,
                    params,
                    model_type,
                    eval_file_pattern=None,
                    batch_size=4,
                    eval_steps=None,
                    model_dir=None,
                    timeout=3000):
  """Continuously evaluate checkpoints on testing data."""
  test_dataset = input_pipeline.get_input_dataset(
      eval_file_pattern,
      batch_size=batch_size,
      params=params,
      is_training=False,
      strategy=strategy)

  with strategy.scope():
    model = models.create_model(model_type, params)
    metric_layer = metrics_v2.MetricLayer(params.vocab_size)
    eval_summary_writer = tf.summary.create_file_writer(
        os.path.join(model_dir, "summaries/eval"))
    global_step = tf.Variable(
        0,
        trainable=False,
        dtype=tf.int64,
        aggregation=tf.VariableAggregation.ONLY_FIRST_REPLICA,
        shape=[])

  @tf.function
  def test_step(inputs):
    """Calculates evaluation metrics on distributed devices."""

    def _test_step_fn(inputs):
      """Replicated accuracy calculation."""
      targets = models.remove_sos_from_seq(inputs["target_ids"],
                                           params.pad_token_id)

      # Using ground truth sequences as targets to calculate logits for accuracy
      # and perplexity metrics.
      logits, _, _ = model(inputs, training=False, mode="train")
      metric_layer([logits, targets])

      # Get logits from top beam search results for bleu and rouge metrics.
      logits = model(inputs, training=False, mode="eval")

      return targets, logits

    outputs = strategy.run(_test_step_fn, args=(inputs,))

    return tf.nest.map_structure(strategy.experimental_local_results, outputs)

  metrics_and_funcs = [
      (tf_keras.metrics.Mean("bleu", dtype=tf.float32), bleu_score),
      (tf_keras.metrics.Mean("rouge_2_fscore",
                             dtype=tf.float32), rouge_2_fscore),
      (tf_keras.metrics.Mean("rouge_l_fscore",
                             dtype=tf.float32), rouge_l_fscore),
  ]
  eval_results = {}
  for latest_checkpoint in tf.train.checkpoints_iterator(
      model_dir, timeout=timeout):
    checkpoint = tf.train.Checkpoint(model=model, global_step=global_step)
    checkpoint.restore(latest_checkpoint).expect_partial()
    logging.info("Loaded checkpoint %s", latest_checkpoint)

    for i, inputs in enumerate(test_dataset):
      if eval_steps and i >= eval_steps:
        break
      outputs = test_step(inputs)
      for metric, func in metrics_and_funcs:
        for targets, logits in zip(outputs[0], outputs[1]):
          metric.update_state(func(logits.numpy(), targets.numpy()))

    with eval_summary_writer.as_default():
      step = global_step.numpy()
      for metric, _ in metrics_and_funcs:
        eval_results[metric.name] = metric.result().numpy().astype(float)
        tf.summary.scalar(
            metric.name,
            eval_results[metric.name],
            step=step)
      for metric in metric_layer.metrics:
        eval_results[metric.name] = metric.result().numpy().astype(float)
        tf.summary.scalar(
            metric.name,
            eval_results[metric.name],
            step=step)
      logging.info("Step %d Metrics= %s", step, str(eval_results))
      eval_summary_writer.flush()

    # Resets metrics.
    for metric, _ in metrics_and_funcs:
      metric.reset_states()
    for metric in metric_layer.metrics:
      metric.reset_states()
  return eval_results