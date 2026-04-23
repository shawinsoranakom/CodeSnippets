def run_evaluation(strategy, test_input_fn, eval_examples, eval_features,
                   original_data, eval_steps, input_meta_data, model,
                   current_step, eval_summary_writer):
  """Run evaluation for SQUAD task.

  Args:
    strategy: distribution strategy.
    test_input_fn: input function for evaluation data.
    eval_examples: tf.Examples of the evaluation set.
    eval_features: Feature objects of the evaluation set.
    original_data: The original json data for the evaluation set.
    eval_steps: total number of evaluation steps.
    input_meta_data: input meta data.
    model: keras model object.
    current_step: current training step.
    eval_summary_writer: summary writer used to record evaluation metrics.

  Returns:
    A float metric, F1 score.
  """

  def _test_step_fn(inputs):
    """Replicated validation step."""

    inputs["mems"] = None
    res = model(inputs, training=False)
    return res, inputs["unique_ids"]

  @tf.function
  def _run_evaluation(test_iterator):
    """Runs validation steps."""
    res, unique_ids = strategy.run(
        _test_step_fn, args=(next(test_iterator),))
    return res, unique_ids

  test_iterator = data_utils.get_input_iterator(test_input_fn, strategy)
  cur_results = []
  for _ in range(eval_steps):
    results, unique_ids = _run_evaluation(test_iterator)
    unique_ids = strategy.experimental_local_results(unique_ids)

    for result_key in results:
      results[result_key] = (
          strategy.experimental_local_results(results[result_key]))
    for core_i in range(strategy.num_replicas_in_sync):
      bsz = int(input_meta_data["test_batch_size"] /
                strategy.num_replicas_in_sync)
      for j in range(bsz):
        result = {}
        for result_key in results:
          result[result_key] = results[result_key][core_i].numpy()[j]
        result["unique_ids"] = unique_ids[core_i].numpy()[j]
        # We appended a fake example into dev set to make data size can be
        # divided by test_batch_size. Ignores this fake example during
        # evaluation.
        if result["unique_ids"] == 1000012047:
          continue
        unique_id = int(result["unique_ids"])

        start_top_log_probs = ([
            float(x) for x in result["start_top_log_probs"].flat
        ])
        start_top_index = [int(x) for x in result["start_top_index"].flat]
        end_top_log_probs = ([
            float(x) for x in result["end_top_log_probs"].flat
        ])
        end_top_index = [int(x) for x in result["end_top_index"].flat]

        cls_logits = float(result["cls_logits"].flat[0])
        cur_results.append(
            squad_utils.RawResult(
                unique_id=unique_id,
                start_top_log_probs=start_top_log_probs,
                start_top_index=start_top_index,
                end_top_log_probs=end_top_log_probs,
                end_top_index=end_top_index,
                cls_logits=cls_logits))
        if len(cur_results) % 1000 == 0:
          logging.info("Processing example: %d", len(cur_results))

  output_prediction_file = os.path.join(input_meta_data["predict_dir"],
                                        "predictions.json")
  output_nbest_file = os.path.join(input_meta_data["predict_dir"],
                                   "nbest_predictions.json")
  output_null_log_odds_file = os.path.join(input_meta_data["predict_dir"],
                                           "null_odds.json")

  results = squad_utils.write_predictions(
      eval_examples, eval_features, cur_results, input_meta_data["n_best_size"],
      input_meta_data["max_answer_length"], output_prediction_file,
      output_nbest_file, output_null_log_odds_file, original_data,
      input_meta_data["start_n_top"], input_meta_data["end_n_top"])

  # Log current results.
  log_str = "Result | "
  for key, val in results.items():
    log_str += "{} {} | ".format(key, val)
  logging.info(log_str)
  with eval_summary_writer.as_default():
    tf.summary.scalar("best_f1", results["best_f1"], step=current_step)
    tf.summary.scalar("best_exact", results["best_exact"], step=current_step)
    eval_summary_writer.flush()
  return results["best_f1"]