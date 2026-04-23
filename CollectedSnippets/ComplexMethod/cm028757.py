def postprocess_output(all_examples,
                       all_features,
                       all_results,
                       n_best_size,
                       max_answer_length,
                       do_lower_case,
                       version_2_with_negative=False,
                       null_score_diff_threshold=0.0,
                       xlnet_format=False,
                       verbose=False):
  """Postprocess model output, to form predicton results."""

  del do_lower_case, verbose
  example_index_to_features = collections.defaultdict(list)
  for feature in all_features:
    example_index_to_features[feature.example_index].append(feature)

  unique_id_to_result = {}
  for result in all_results:
    unique_id_to_result[result.unique_id] = result

  _PrelimPrediction = collections.namedtuple(  # pylint: disable=invalid-name
      "PrelimPrediction",
      ["feature_index", "start_index", "end_index", "start_logit", "end_logit"])

  all_predictions = collections.OrderedDict()
  all_nbest_json = collections.OrderedDict()
  scores_diff_json = collections.OrderedDict()

  for (example_index, example) in enumerate(all_examples):
    features = example_index_to_features[example_index]

    prelim_predictions = []
    # keep track of the minimum score of null start+end of position 0
    score_null = 1000000  # large and positive
    min_null_feature_index = 0  # the paragraph slice with min mull score
    null_start_logit = 0  # the start logit at the slice with min null score
    null_end_logit = 0  # the end logit at the slice with min null score
    for (feature_index, feature) in enumerate(features):
      if feature.unique_id not in unique_id_to_result:
        logging.info("Skip eval example %s, not in pred.", feature.unique_id)
        continue
      result = unique_id_to_result[feature.unique_id]

      # if we could have irrelevant answers, get the min score of irrelevant
      if version_2_with_negative:
        if xlnet_format:
          feature_null_score = result.class_logits
        else:
          feature_null_score = result.start_logits[0] + result.end_logits[0]
        if feature_null_score < score_null:
          score_null = feature_null_score
          min_null_feature_index = feature_index
          null_start_logit = result.start_logits[0]
          null_end_logit = result.end_logits[0]

      doc_offset = 0 if xlnet_format else feature.tokens.index("[SEP]") + 1

      for (start_index, start_logit,
           end_index, end_logit) in _get_best_indexes_and_logits(
               result=result,
               n_best_size=n_best_size,
               xlnet_format=xlnet_format):
        # We could hypothetically create invalid predictions, e.g., predict
        # that the start of the span is in the question. We throw out all
        # invalid predictions.
        if start_index - doc_offset >= len(feature.tok_start_to_orig_index):
          continue
        if end_index - doc_offset >= len(feature.tok_end_to_orig_index):
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
                start_index=start_index - doc_offset,
                end_index=end_index - doc_offset,
                start_logit=start_logit,
                end_logit=end_logit))

    if version_2_with_negative and not xlnet_format:
      prelim_predictions.append(
          _PrelimPrediction(
              feature_index=min_null_feature_index,
              start_index=-1,
              end_index=-1,
              start_logit=null_start_logit,
              end_logit=null_end_logit))
    prelim_predictions = sorted(
        prelim_predictions,
        key=lambda x: (x.start_logit + x.end_logit),
        reverse=True)

    _NbestPrediction = collections.namedtuple(  # pylint: disable=invalid-name
        "NbestPrediction", ["text", "start_logit", "end_logit"])

    seen_predictions = {}
    nbest = []
    for pred in prelim_predictions:
      if len(nbest) >= n_best_size:
        break
      feature = features[pred.feature_index]
      if pred.start_index >= 0 or xlnet_format:  # this is a non-null prediction
        tok_start_to_orig_index = feature.tok_start_to_orig_index
        tok_end_to_orig_index = feature.tok_end_to_orig_index
        start_orig_pos = tok_start_to_orig_index[pred.start_index]
        end_orig_pos = tok_end_to_orig_index[pred.end_index]

        paragraph_text = example.paragraph_text
        final_text = paragraph_text[start_orig_pos:end_orig_pos + 1].strip()
        if final_text in seen_predictions:
          continue

        seen_predictions[final_text] = True
      else:
        final_text = ""
        seen_predictions[final_text] = True

      nbest.append(
          _NbestPrediction(
              text=final_text,
              start_logit=pred.start_logit,
              end_logit=pred.end_logit))

    # if we didn't include the empty option in the n-best, include it
    if version_2_with_negative and not xlnet_format:
      if "" not in seen_predictions:
        nbest.append(
            _NbestPrediction(
                text="", start_logit=null_start_logit,
                end_logit=null_end_logit))
    # In very rare edge cases we could have no valid predictions. So we
    # just create a nonce prediction in this case to avoid failure.
    if not nbest:
      nbest.append(
          _NbestPrediction(text="empty", start_logit=0.0, end_logit=0.0))

    assert len(nbest) >= 1

    total_scores = []
    best_non_null_entry = None
    for entry in nbest:
      total_scores.append(entry.start_logit + entry.end_logit)
      if not best_non_null_entry:
        if entry.text:
          best_non_null_entry = entry

    probs = _compute_softmax(total_scores)

    nbest_json = []
    for (i, entry) in enumerate(nbest):
      output = collections.OrderedDict()
      output["text"] = entry.text
      output["probability"] = probs[i]
      output["start_logit"] = entry.start_logit
      output["end_logit"] = entry.end_logit
      nbest_json.append(output)

    assert len(nbest_json) >= 1

    if not version_2_with_negative:
      all_predictions[example.qas_id] = nbest_json[0]["text"]
    else:
      assert best_non_null_entry is not None
      if xlnet_format:
        score_diff = score_null
        scores_diff_json[example.qas_id] = score_diff
        all_predictions[example.qas_id] = best_non_null_entry.text
      else:
        # predict "" iff the null score - the score of best non-null > threshold
        score_diff = score_null - best_non_null_entry.start_logit - (
            best_non_null_entry.end_logit)
        scores_diff_json[example.qas_id] = score_diff
        if score_diff > null_score_diff_threshold:
          all_predictions[example.qas_id] = ""
        else:
          all_predictions[example.qas_id] = best_non_null_entry.text

    all_nbest_json[example.qas_id] = nbest_json

  return all_predictions, all_nbest_json, scores_diff_json