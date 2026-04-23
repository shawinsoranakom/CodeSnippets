def realign_answer_span(features: Features, answer_set: Optional[Set[Text]],
                        processor: spm.SentencePieceProcessor,
                        span: AnswerSpan) -> Optional[AnswerSpan]:
  """Align answer span to text with given tokens."""
  i = bisect.bisect_left(features.token_offsets, span.begin)
  if i == len(features.token_offsets) or span.begin < features.token_offsets[i]:
    i -= 1
  j = i + 1
  answer_end = span.begin + len(span.text.encode('utf-8'))
  while (j < len(features.token_offsets) and
         features.token_offsets[j] < answer_end):
    j += 1
  j -= 1
  sp_answer = (
      features.context[features.token_offsets[i]:features.token_offsets[j + 1]]
      if j + 1 < len(features.token_offsets) else
      features.context[features.token_offsets[i]:])
  if (processor.IdToPiece(features.token_ids[i]).startswith('▁') and
      features.token_offsets[i] > 0):
    sp_answer = sp_answer[1:]
  sp_answer = evaluation.normalize_answer(sp_answer.decode('utf-8'))
  if answer_set is not None and sp_answer not in answer_set:
    # No need to warn if the cause was breaking word boundaries.
    if len(sp_answer) and not len(sp_answer) > len(
        evaluation.normalize_answer(span.text)):
      logging.warning('%s: "%s" not in %s.', features.question_id, sp_answer,
                      answer_set)
    return None
  return AnswerSpan(begin=i, end=j, text=span.text)