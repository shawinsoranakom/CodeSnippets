def evaluate(dataset, predictions, na_probs=None):
  """Evaluate prediction results."""
  new_orig_data = []
  for article in dataset:
    for p in article['paragraphs']:
      for qa in p['qas']:
        if qa['id'] in predictions:
          new_para = {'qas': [qa]}
          new_article = {'paragraphs': [new_para]}
          new_orig_data.append(new_article)
  dataset = new_orig_data

  if na_probs is None:
    na_probs = {k: 0.0 for k in predictions}
  qid_to_has_ans = _make_qid_to_has_ans(dataset)  # maps qid to True/False
  has_ans_qids = [k for k, v in qid_to_has_ans.items() if v]
  no_ans_qids = [k for k, v in qid_to_has_ans.items() if not v]
  exact_raw, f1_raw = _get_raw_scores(dataset, predictions)
  exact_thresh = _apply_no_ans_threshold(exact_raw, na_probs, qid_to_has_ans)
  f1_thresh = _apply_no_ans_threshold(f1_raw, na_probs, qid_to_has_ans)
  out_eval = _make_eval_dict(exact_thresh, f1_thresh)
  if has_ans_qids:
    has_ans_eval = _make_eval_dict(
        exact_thresh, f1_thresh, qid_list=has_ans_qids)
    _merge_eval(out_eval, has_ans_eval, 'HasAns')
  if no_ans_qids:
    no_ans_eval = _make_eval_dict(exact_thresh, f1_thresh, qid_list=no_ans_qids)
    _merge_eval(out_eval, no_ans_eval, 'NoAns')

  _find_all_best_thresh(
      out_eval, predictions, exact_raw, f1_raw, na_probs, qid_to_has_ans)
  _run_precision_recall_analysis(
      out_eval, exact_raw, f1_raw, na_probs, qid_to_has_ans)
  return out_eval