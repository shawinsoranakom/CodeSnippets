def evaluate_triviaqa(ground_truth,
                      predicted_answers,
                      qid_list=None,
                      mute=False):
  f1 = exact_match = common = 0
  if qid_list is None:
    qid_list = ground_truth.keys()
  for qid in qid_list:
    if qid not in predicted_answers:
      if not mute:
        message = 'Missed question {} will receive score 0.'.format(qid)
        print(message, file=sys.stderr)
      continue
    if qid not in ground_truth:
      if not mute:
        message = 'Irrelavant question {} will receive score 0.'.format(qid)
        print(message, file=sys.stderr)
      continue
    common += 1
    prediction = predicted_answers[qid]
    ground_truths = get_ground_truths(ground_truth[qid])
    em_for_this_question = metric_max_over_ground_truths(
        exact_match_score, prediction, ground_truths)
    if em_for_this_question == 0 and not mute:
      print('em=0:', prediction, ground_truths)
    exact_match += em_for_this_question
    f1_for_this_question = metric_max_over_ground_truths(
        f1_score, prediction, ground_truths)
    f1 += f1_for_this_question

  exact_match = 100.0 * exact_match / len(qid_list)
  f1 = 100.0 * f1 / len(qid_list)

  return {
      'exact_match': exact_match,
      'f1': f1,
      'common': common,
      'denominator': len(qid_list),
      'pred_len': len(predicted_answers),
      'gold_len': len(ground_truth)
  }