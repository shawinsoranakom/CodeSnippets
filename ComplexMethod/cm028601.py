def _make_features(self, stride_index: int, paragraph_texts: List[Text],
                     paragraphs: List[Paragraph],
                     question_answer_evidence: QuestionAnswerEvidence,
                     ids: List[int],
                     paragraph_offset: int) -> Tuple[int, Features]:
    global_ids = (
        [self._sentencepiece_processor.PieceToId(_CLS_PIECE)] +
        [self._sentencepiece_processor.PieceToId(_QUESTION_PIECE)] * len(ids))
    segment_ids = [i + 1 for i in range(len(ids))]  # offset for CLS token
    token_ids, sentences = [], []
    offsets, offset, full_text = [-1] * len(ids), 0, True
    for i in range(paragraph_offset, len(paragraph_texts)):
      if i < len(paragraphs):
        paragraph = paragraphs[i]
      else:
        paragraphs.append(
            make_paragraph(
                self._sentence_tokenizer,
                self._sentencepiece_processor,
                paragraph_texts[i],
                paragraph_metric=metrics.Metrics.distribution(
                    '_', 'paragraphs'),
                sentence_metric=metrics.Metrics.distribution('_', 'sentences')))
        paragraph = paragraphs[-1]
      for sentence in paragraph.sentences:
        if (len(ids) + len(token_ids) + len(sentence.pieces) + 1 >=
            self._max_num_tokens or
            len(global_ids) >= self._max_num_global_tokens):
          full_text = False
          break
        for j, piece in enumerate(sentence.pieces):
          token_ids.append(piece.id)
          segment_ids.append(len(global_ids))
          offsets.append(offset + piece.begin)
          if j == 0 and sentences:
            offsets[-1] -= 1
        offset += len(sentence.text.encode('utf-8')) + 1
        global_ids.append(self._sentencepiece_processor.PieceToId(_EOS_PIECE))
        sentences.append(sentence.text)
      if not full_text:
        break
    context = ' '.join(sentences).encode('utf-8')
    token_ids.append(self._sentencepiece_processor.PieceToId(_NULL_PIECE))
    offsets.append(len(context))
    segment_ids.append(0)
    next_paragraph_index = len(paragraph_texts)
    if not full_text and self._stride > 0:
      shift = paragraphs[paragraph_offset].size
      next_paragraph_index = paragraph_offset + 1
      while (next_paragraph_index < len(paragraphs) and
             shift + paragraphs[next_paragraph_index].size <= self._stride):
        shift += paragraphs[next_paragraph_index].size
        next_paragraph_index += 1
    return next_paragraph_index, Features(
        id='{}--{}'.format(question_answer_evidence.question.id,
                           question_answer_evidence.evidence.info.id),
        stride_index=stride_index,
        question_id=question_answer_evidence.question.id,
        question=question_answer_evidence.question.value,
        context=context,
        token_ids=ids + token_ids,
        global_token_ids=global_ids,
        segment_ids=segment_ids,
        token_offsets=offsets)