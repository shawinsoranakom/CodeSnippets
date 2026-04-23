def convert_examples_to_features(examples,
                                 tokenizer,
                                 max_seq_length,
                                 doc_stride,
                                 max_query_length,
                                 is_training,
                                 output_fn,
                                 xlnet_format=False,
                                 batch_size=None):
  """Loads a data file into a list of `InputBatch`s."""

  base_id = 1000000000
  unique_id = base_id
  feature = None
  for (example_index, example) in enumerate(examples):
    query_tokens = tokenizer.tokenize(example.question_text)

    if len(query_tokens) > max_query_length:
      query_tokens = query_tokens[0:max_query_length]

    tok_to_orig_index = []
    orig_to_tok_index = []
    all_doc_tokens = []
    for (i, token) in enumerate(example.doc_tokens):
      orig_to_tok_index.append(len(all_doc_tokens))
      sub_tokens = tokenizer.tokenize(token)
      for sub_token in sub_tokens:
        tok_to_orig_index.append(i)
        all_doc_tokens.append(sub_token)

    tok_start_position = None
    tok_end_position = None
    if is_training and example.is_impossible:
      tok_start_position = -1
      tok_end_position = -1
    if is_training and not example.is_impossible:
      tok_start_position = orig_to_tok_index[example.start_position]
      if example.end_position < len(example.doc_tokens) - 1:
        tok_end_position = orig_to_tok_index[example.end_position + 1] - 1
      else:
        tok_end_position = len(all_doc_tokens) - 1
      (tok_start_position, tok_end_position) = _improve_answer_span(
          all_doc_tokens, tok_start_position, tok_end_position, tokenizer,
          example.orig_answer_text)

    # The -3 accounts for [CLS], [SEP] and [SEP]
    max_tokens_for_doc = max_seq_length - len(query_tokens) - 3

    # We can have documents that are longer than the maximum sequence length.
    # To deal with this we do a sliding window approach, where we take chunks
    # of the up to our max length with a stride of `doc_stride`.
    _DocSpan = collections.namedtuple(  # pylint: disable=invalid-name
        "DocSpan", ["start", "length"])
    doc_spans = []
    start_offset = 0
    while start_offset < len(all_doc_tokens):
      length = len(all_doc_tokens) - start_offset
      if length > max_tokens_for_doc:
        length = max_tokens_for_doc
      doc_spans.append(_DocSpan(start=start_offset, length=length))
      if start_offset + length == len(all_doc_tokens):
        break
      start_offset += min(length, doc_stride)

    for (doc_span_index, doc_span) in enumerate(doc_spans):
      tokens = []
      token_to_orig_map = {}
      token_is_max_context = {}
      segment_ids = []

      # Paragraph mask used in XLNet.
      # 1 represents paragraph and class tokens.
      # 0 represents query and other special tokens.
      paragraph_mask = []

      # pylint: disable=cell-var-from-loop
      def process_query(seg_q):
        for token in query_tokens:
          tokens.append(token)
          segment_ids.append(seg_q)
          paragraph_mask.append(0)
        tokens.append("[SEP]")
        segment_ids.append(seg_q)
        paragraph_mask.append(0)

      def process_paragraph(seg_p):
        for i in range(doc_span.length):
          split_token_index = doc_span.start + i
          token_to_orig_map[len(tokens)] = tok_to_orig_index[split_token_index]

          is_max_context = _check_is_max_context(doc_spans, doc_span_index,
                                                 split_token_index)
          token_is_max_context[len(tokens)] = is_max_context
          tokens.append(all_doc_tokens[split_token_index])
          segment_ids.append(seg_p)
          paragraph_mask.append(1)
        tokens.append("[SEP]")
        segment_ids.append(seg_p)
        paragraph_mask.append(0)

      def process_class(seg_class):
        class_index = len(segment_ids)
        tokens.append("[CLS]")
        segment_ids.append(seg_class)
        paragraph_mask.append(1)
        return class_index

      if xlnet_format:
        seg_p, seg_q, seg_class, seg_pad = 0, 1, 2, 3
        process_paragraph(seg_p)
        process_query(seg_q)
        class_index = process_class(seg_class)
      else:
        seg_p, seg_q, seg_class, seg_pad = 1, 0, 0, 0
        class_index = process_class(seg_class)
        process_query(seg_q)
        process_paragraph(seg_p)

      input_ids = tokenizer.convert_tokens_to_ids(tokens)

      # The mask has 1 for real tokens and 0 for padding tokens. Only real
      # tokens are attended to.
      input_mask = [1] * len(input_ids)

      # Zero-pad up to the sequence length.
      while len(input_ids) < max_seq_length:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(seg_pad)
        paragraph_mask.append(0)

      assert len(input_ids) == max_seq_length
      assert len(input_mask) == max_seq_length
      assert len(segment_ids) == max_seq_length
      assert len(paragraph_mask) == max_seq_length

      start_position = 0
      end_position = 0
      span_contains_answer = False

      if is_training and not example.is_impossible:
        # For training, if our document chunk does not contain an annotation
        # we throw it out, since there is nothing to predict.
        doc_start = doc_span.start
        doc_end = doc_span.start + doc_span.length - 1
        span_contains_answer = (tok_start_position >= doc_start and
                                tok_end_position <= doc_end)
        if span_contains_answer:
          doc_offset = 0 if xlnet_format else len(query_tokens) + 2
          start_position = tok_start_position - doc_start + doc_offset
          end_position = tok_end_position - doc_start + doc_offset

      if example_index < 20:
        logging.info("*** Example ***")
        logging.info("unique_id: %s", (unique_id))
        logging.info("example_index: %s", (example_index))
        logging.info("doc_span_index: %s", (doc_span_index))
        logging.info("tokens: %s",
                     " ".join([tokenization.printable_text(x) for x in tokens]))
        logging.info(
            "token_to_orig_map: %s", " ".join([
                "%d:%d" % (x, y) for (x, y) in six.iteritems(token_to_orig_map)
            ]))
        logging.info(
            "token_is_max_context: %s", " ".join([
                "%d:%s" % (x, y)
                for (x, y) in six.iteritems(token_is_max_context)
            ]))
        logging.info("input_ids: %s", " ".join([str(x) for x in input_ids]))
        logging.info("input_mask: %s", " ".join([str(x) for x in input_mask]))
        logging.info("segment_ids: %s", " ".join([str(x) for x in segment_ids]))
        logging.info("paragraph_mask: %s", " ".join(
            [str(x) for x in paragraph_mask]))
        logging.info("class_index: %d", class_index)
        if is_training:
          if span_contains_answer:
            answer_text = " ".join(tokens[start_position:(end_position + 1)])
            logging.info("start_position: %d", (start_position))
            logging.info("end_position: %d", (end_position))
            logging.info("answer: %s", tokenization.printable_text(answer_text))
          else:
            logging.info("document span doesn't contain answer")

      feature = InputFeatures(
          unique_id=unique_id,
          example_index=example_index,
          doc_span_index=doc_span_index,
          tokens=tokens,
          paragraph_mask=paragraph_mask,
          class_index=class_index,
          token_to_orig_map=token_to_orig_map,
          token_is_max_context=token_is_max_context,
          input_ids=input_ids,
          input_mask=input_mask,
          segment_ids=segment_ids,
          start_position=start_position,
          end_position=end_position,
          is_impossible=not span_contains_answer)

      # Run callback
      if is_training:
        output_fn(feature)
      else:
        output_fn(feature, is_padding=False)

      unique_id += 1

  if not is_training and feature:
    assert batch_size
    num_padding = 0
    num_examples = unique_id - base_id
    if unique_id % batch_size != 0:
      num_padding = batch_size - (num_examples % batch_size)
    logging.info("Adding padding examples to make sure no partial batch.")
    logging.info("Adds %d padding examples for inference.", num_padding)
    dummy_feature = copy.deepcopy(feature)
    for _ in range(num_padding):
      dummy_feature.unique_id = unique_id

      # Run callback
      output_fn(feature, is_padding=True)
      unique_id += 1
  return unique_id - base_id