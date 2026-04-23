def write_predictions(all_examples, all_features, all_results, n_best_size,
                      max_answer_length, output_prediction_file,
                      output_nbest_file, output_null_log_odds_file, orig_data,
                      start_n_top, end_n_top):
  """Writes final predictions to the json file and log-odds of null if needed."""
  logging.info("Writing predictions to: %s", (output_prediction_file))

  example_index_to_features = collections.defaultdict(list)
  for feature in all_features:
    example_index_to_features[feature.example_index].append(feature)

  unique_id_to_result = {}
  for result in all_results:
    unique_id_to_result[result.unique_id] = result

  all_predictions = collections.OrderedDict()
  all_nbest_json = collections.OrderedDict()
  scores_diff_json = collections.OrderedDict()

  for (example_index, example) in enumerate(all_examples):
    features = example_index_to_features[example_index]

    prelim_predictions = []
    # keep track of the minimum score of null start+end of position 0
    score_null = 1000000  # large and positive

    for (feature_index, feature) in enumerate(features):
      result = unique_id_to_result[feature.unique_id]

      cur_null_score = result.cls_logits

      # if we could have irrelevant answers, get the min score of irrelevant
      score_null = min(score_null, cur_null_score)

      for i in range(start_n_top):
        for j in range(end_n_top):
          start_log_prob = result.start_top_log_probs[i]
          start_index = result.start_top_index[i]

          j_index = i * end_n_top + j

          end_log_prob = result.end_top_log_probs[j_index]
          end_index = result.end_top_index[j_index]

          # We could hypothetically create invalid predictions, e.g., predict
          # that the start of the span is in the question. We throw out all
          # invalid predictions.
          if start_index >= feature.paragraph_len - 1:
            continue
          if end_index >= feature.paragraph_len - 1:
            continue

          if not feature.token_is_max_context.get(start_index, False):
            continue
          if end_index < start_index:
            continue
          length = end_index - start_index + 1
          if length > max_answer_length:
            continue

          prelim_predictions.append(
              _PrelimPrediction(
                  feature_index=feature_index,
                  start_index=start_index,
                  end_index=end_index,
                  start_log_prob=start_log_prob,
                  end_log_prob=end_log_prob))

    prelim_predictions = sorted(
        prelim_predictions,
        key=lambda x: (x.start_log_prob + x.end_log_prob),
        reverse=True)

    seen_predictions = {}
    nbest = []
    for pred in prelim_predictions:
      if len(nbest) >= n_best_size:
        break
      feature = features[pred.feature_index]

      tok_start_to_orig_index = feature.tok_start_to_orig_index
      tok_end_to_orig_index = feature.tok_end_to_orig_index
      start_orig_pos = tok_start_to_orig_index[pred.start_index]
      end_orig_pos = tok_end_to_orig_index[pred.end_index]

      paragraph_text = example.paragraph_text
      final_text = paragraph_text[start_orig_pos:end_orig_pos + 1].strip()

      if final_text in seen_predictions:
        continue

      seen_predictions[final_text] = True

      nbest.append(
          _NbestPrediction(
              text=final_text,
              start_log_prob=pred.start_log_prob,
              end_log_prob=pred.end_log_prob))

    # In very rare edge cases we could have no valid predictions. So we
    # just create a nonce prediction in this case to avoid failure.
    if not nbest:
      nbest.append(
          _NbestPrediction(text="", start_log_prob=-1e6, end_log_prob=-1e6))

    total_scores = []
    best_non_null_entry = None
    for entry in nbest:
      total_scores.append(entry.start_log_prob + entry.end_log_prob)
      if not best_non_null_entry:
        best_non_null_entry = entry

    probs = _compute_softmax(total_scores)

    nbest_json = []
    for (i, entry) in enumerate(nbest):
      output = collections.OrderedDict()
      output["text"] = entry.text
      output["probability"] = probs[i]
      output["start_log_prob"] = entry.start_log_prob
      output["end_log_prob"] = entry.end_log_prob
      nbest_json.append(output)

    assert len(nbest_json) >= 1
    assert best_non_null_entry is not None

    score_diff = score_null
    scores_diff_json[example.qas_id] = score_diff

    all_predictions[example.qas_id] = best_non_null_entry.text

    all_nbest_json[example.qas_id] = nbest_json

  with tf.io.gfile.GFile(output_prediction_file, "w") as writer:
    writer.write(json.dumps(all_predictions, indent=4) + "\n")

  with tf.io.gfile.GFile(output_nbest_file, "w") as writer:
    writer.write(json.dumps(all_nbest_json, indent=4) + "\n")

  with tf.io.gfile.GFile(output_null_log_odds_file, "w") as writer:
    writer.write(json.dumps(scores_diff_json, indent=4) + "\n")

  qid_to_has_ans = make_qid_to_has_ans(orig_data)
  exact_raw, f1_raw = get_raw_scores(orig_data, all_predictions)
  out_eval = {}

  find_all_best_thresh(out_eval, all_predictions, exact_raw, f1_raw,
                       scores_diff_json, qid_to_has_ans)

  return out_eval