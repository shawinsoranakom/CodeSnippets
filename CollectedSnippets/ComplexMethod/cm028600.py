def _handle_exceptional_examples(
    features: Features,
    processor: spm.SentencePieceProcessor) -> List[AnswerSpan]:
  """Special cases in data."""
  if features.id == 'qw_6687--Viola.txt':
    pattern = 'three strings in common—G, D, and A'.encode('utf-8')
    i = features.context.find(pattern)
    if i != -1:
      span = AnswerSpan(i + len(pattern) - 1, i + len(pattern), 'A')
      span = realign_answer_span(features, None, processor, span)
      assert span is not None, 'Span should exist.'
      return [span]
  if features.id == 'sfq_26183--Vitamin_A.txt':
    pattern = ('Vitamin A is a group of unsaturated nutritional organic '
               'compounds that includes retinol').encode('utf-8')
    i = features.context.find(pattern)
    if i != -1:
      span = AnswerSpan(i + pattern.find(b'A'), i + pattern.find(b'A') + 1, 'A')
      span = realign_answer_span(features, None, processor, span)
      assert span is not None, 'Span should exist.'
      spans = [span]
      span = AnswerSpan(i, i + pattern.find(b'A') + 1, 'Vitamin A')
      span = realign_answer_span(features, None, processor, span)
      return spans + [span]
  if features.id == 'odql_292--Colombia.txt':
    pattern = b'Colombia is the third-most populous country in Latin America'
    i = features.context.find(pattern)
    if i != -1:
      span = AnswerSpan(i, i + len(b'Colombia'), 'Colombia')
      span = realign_answer_span(features, None, processor, span)
      assert span is not None, 'Span should exist.'
      return [span]
  if features.id == 'tc_1648--Vietnam.txt':
    pattern = 'Bảo Đại'.encode('utf-8')
    i = features.context.find(pattern)
    if i != -1:
      span = AnswerSpan(i, i + len(pattern), 'Bảo Đại')
      span = realign_answer_span(features, None, processor, span)
      assert span is not None, 'Span should exist.'
      return [span]
  if features.id == 'sfq_22225--Irish_mythology.txt':
    pattern = 'Tír na nÓg'.encode('utf-8')
    spans = []
    i = 0
    while features.context.find(pattern, i) != -1:
      i = features.context.find(pattern)
      span = AnswerSpan(i, i + len(pattern), 'Tír na nÓg')
      span = realign_answer_span(features, None, processor, span)
      assert span is not None, 'Span should exist.'
      spans.append(span)
      i += len(pattern)
    return spans
  return []