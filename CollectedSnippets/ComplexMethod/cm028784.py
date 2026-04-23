def _get_raw_scores(dataset, predictions):
  """Compute raw scores."""
  exact_scores = {}
  f1_scores = {}
  for article in dataset:
    for p in article['paragraphs']:
      for qa in p['qas']:
        qid = qa['id']
        gold_answers = [a['text'] for a in qa['answers']
                        if _normalize_answer(a['text'])]
        if not gold_answers:
          # For unanswerable questions, only correct answer is empty string
          gold_answers = ['']
        if qid not in predictions:
          logging.error('Missing prediction for %s', qid)
          continue
        a_pred = predictions[qid]
        # Take max over all gold answers
        exact_scores[qid] = max(_compute_exact(a, a_pred) for a in gold_answers)
        f1_scores[qid] = max(_compute_f1(a, a_pred) for a in gold_answers)
  return exact_scores, f1_scores