def convert_examples_to_features(examples,
                                 tokenizer,
                                 max_seq_length,
                                 doc_stride,
                                 max_query_length,
                                 is_training,
                                 output_fn,
                                 do_lower_case,
                                 xlnet_format=False,
                                 batch_size=None):
  """Loads a data file into a list of `InputBatch`s."""
  cnt_pos, cnt_neg = 0, 0
  base_id = 1000000000
  unique_id = base_id
  max_n, max_m = 1024, 1024
  f = np.zeros((max_n, max_m), dtype=np.float32)

  for (example_index, example) in enumerate(examples):

    if example_index % 100 == 0:
      logging.info("Converting %d/%d pos %d neg %d", example_index,
                   len(examples), cnt_pos, cnt_neg)

    query_tokens = tokenization.encode_ids(
        tokenizer.sp_model,
        tokenization.preprocess_text(
            example.question_text, lower=do_lower_case))

    if len(query_tokens) > max_query_length:
      query_tokens = query_tokens[0:max_query_length]

    paragraph_text = example.paragraph_text
    para_tokens = tokenization.encode_pieces(
        tokenizer.sp_model,
        tokenization.preprocess_text(
            example.paragraph_text, lower=do_lower_case))

    chartok_to_tok_index = []
    tok_start_to_chartok_index = []
    tok_end_to_chartok_index = []
    char_cnt = 0
    for i, token in enumerate(para_tokens):
      new_token = token.replace(tokenization.SPIECE_UNDERLINE, " ")
      chartok_to_tok_index.extend([i] * len(new_token))
      tok_start_to_chartok_index.append(char_cnt)
      char_cnt += len(new_token)
      tok_end_to_chartok_index.append(char_cnt - 1)

    tok_cat_text = "".join(para_tokens).replace(tokenization.SPIECE_UNDERLINE,
                                                " ")
    n, m = len(paragraph_text), len(tok_cat_text)

    if n > max_n or m > max_m:
      max_n = max(n, max_n)
      max_m = max(m, max_m)
      f = np.zeros((max_n, max_m), dtype=np.float32)

    g = {}

    # pylint: disable=cell-var-from-loop
    def _lcs_match(max_dist, n=n, m=m):
      """Longest-common-substring algorithm."""
      f.fill(0)
      g.clear()

      ### longest common sub sequence
      # f[i, j] = max(f[i - 1, j], f[i, j - 1], f[i - 1, j - 1] + match(i, j))
      for i in range(n):

        # unlike standard LCS, this is specifically optimized for the setting
        # because the mismatch between sentence pieces and original text will
        # be small
        for j in range(i - max_dist, i + max_dist):
          if j >= m or j < 0:
            continue

          if i > 0:
            g[(i, j)] = 0
            f[i, j] = f[i - 1, j]

          if j > 0 and f[i, j - 1] > f[i, j]:
            g[(i, j)] = 1
            f[i, j] = f[i, j - 1]

          f_prev = f[i - 1, j - 1] if i > 0 and j > 0 else 0
          if (tokenization.preprocess_text(
              paragraph_text[i], lower=do_lower_case,
              remove_space=False) == tok_cat_text[j] and f_prev + 1 > f[i, j]):
            g[(i, j)] = 2
            f[i, j] = f_prev + 1

    # pylint: enable=cell-var-from-loop

    max_dist = abs(n - m) + 5
    for _ in range(2):
      _lcs_match(max_dist)
      if f[n - 1, m - 1] > 0.8 * n:
        break
      max_dist *= 2

    orig_to_chartok_index = [None] * n
    chartok_to_orig_index = [None] * m
    i, j = n - 1, m - 1
    while i >= 0 and j >= 0:
      if (i, j) not in g:
        break
      if g[(i, j)] == 2:
        orig_to_chartok_index[i] = j
        chartok_to_orig_index[j] = i
        i, j = i - 1, j - 1
      elif g[(i, j)] == 1:
        j = j - 1
      else:
        i = i - 1

    if (all(v is None for v in orig_to_chartok_index) or
        f[n - 1, m - 1] < 0.8 * n):
      logging.info("MISMATCH DETECTED!")
      continue

    tok_start_to_orig_index = []
    tok_end_to_orig_index = []
    for i in range(len(para_tokens)):
      start_chartok_pos = tok_start_to_chartok_index[i]
      end_chartok_pos = tok_end_to_chartok_index[i]
      start_orig_pos = _convert_index(
          chartok_to_orig_index, start_chartok_pos, n, is_start=True)
      end_orig_pos = _convert_index(
          chartok_to_orig_index, end_chartok_pos, n, is_start=False)

      tok_start_to_orig_index.append(start_orig_pos)
      tok_end_to_orig_index.append(end_orig_pos)

    if not is_training:
      tok_start_position = tok_end_position = None

    if is_training and example.is_impossible:
      tok_start_position = 0
      tok_end_position = 0

    if is_training and not example.is_impossible:
      start_position = example.start_position
      end_position = start_position + len(example.orig_answer_text) - 1

      start_chartok_pos = _convert_index(
          orig_to_chartok_index, start_position, is_start=True)
      tok_start_position = chartok_to_tok_index[start_chartok_pos]

      end_chartok_pos = _convert_index(
          orig_to_chartok_index, end_position, is_start=False)
      tok_end_position = chartok_to_tok_index[end_chartok_pos]
      assert tok_start_position <= tok_end_position

    def _piece_to_id(x):
      return tokenizer.sp_model.PieceToId(x)

    all_doc_tokens = list(map(_piece_to_id, para_tokens))

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
      token_is_max_context = {}
      segment_ids = []

      # Paragraph mask used in XLNet.
      # 1 represents paragraph and class tokens.
      # 0 represents query and other special tokens.
      paragraph_mask = []

      cur_tok_start_to_orig_index = []
      cur_tok_end_to_orig_index = []

      # pylint: disable=cell-var-from-loop
      def process_query(seg_q):
        for token in query_tokens:
          tokens.append(token)
          segment_ids.append(seg_q)
          paragraph_mask.append(0)
        tokens.append(tokenizer.sp_model.PieceToId("[SEP]"))
        segment_ids.append(seg_q)
        paragraph_mask.append(0)

      def process_paragraph(seg_p):
        for i in range(doc_span.length):
          split_token_index = doc_span.start + i

          cur_tok_start_to_orig_index.append(
              tok_start_to_orig_index[split_token_index])
          cur_tok_end_to_orig_index.append(
              tok_end_to_orig_index[split_token_index])

          is_max_context = _check_is_max_context(doc_spans, doc_span_index,
                                                 split_token_index)
          token_is_max_context[len(tokens)] = is_max_context
          tokens.append(all_doc_tokens[split_token_index])
          segment_ids.append(seg_p)
          paragraph_mask.append(1)
        tokens.append(tokenizer.sp_model.PieceToId("[SEP]"))
        segment_ids.append(seg_p)
        paragraph_mask.append(0)
        return len(tokens)

      def process_class(seg_class):
        class_index = len(segment_ids)
        tokens.append(tokenizer.sp_model.PieceToId("[CLS]"))
        segment_ids.append(seg_class)
        paragraph_mask.append(1)
        return class_index

      if xlnet_format:
        seg_p, seg_q, seg_class, seg_pad = 0, 1, 2, 3
        paragraph_len = process_paragraph(seg_p)
        process_query(seg_q)
        class_index = process_class(seg_class)
      else:
        seg_p, seg_q, seg_class, seg_pad = 1, 0, 0, 0
        class_index = process_class(seg_class)
        process_query(seg_q)
        paragraph_len = process_paragraph(seg_p)

      input_ids = tokens

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

      span_is_impossible = example.is_impossible
      start_position = None
      end_position = None
      if is_training and not span_is_impossible:
        # For training, if our document chunk does not contain an annotation
        # we throw it out, since there is nothing to predict.
        doc_start = doc_span.start
        doc_end = doc_span.start + doc_span.length - 1
        out_of_span = False
        if not (tok_start_position >= doc_start and
                tok_end_position <= doc_end):
          out_of_span = True
        if out_of_span:
          # continue
          start_position = 0
          end_position = 0
          span_is_impossible = True
        else:
          doc_offset = 0 if xlnet_format else len(query_tokens) + 2
          start_position = tok_start_position - doc_start + doc_offset
          end_position = tok_end_position - doc_start + doc_offset

      if is_training and span_is_impossible:
        start_position = class_index
        end_position = class_index

      if example_index < 20:
        logging.info("*** Example ***")
        logging.info("unique_id: %s", (unique_id))
        logging.info("example_index: %s", (example_index))
        logging.info("doc_span_index: %s", (doc_span_index))
        logging.info("tok_start_to_orig_index: %s",
                     " ".join([str(x) for x in cur_tok_start_to_orig_index]))
        logging.info("tok_end_to_orig_index: %s",
                     " ".join([str(x) for x in cur_tok_end_to_orig_index]))
        logging.info(
            "token_is_max_context: %s", " ".join(
                ["%d:%s" % (x, y) for (x, y) in token_is_max_context.items()]))
        logging.info(
            "input_pieces: %s",
            " ".join([tokenizer.sp_model.IdToPiece(x) for x in tokens]))
        logging.info("input_ids: %s", " ".join([str(x) for x in input_ids]))
        logging.info("input_mask: %s", " ".join([str(x) for x in input_mask]))
        logging.info("segment_ids: %s", " ".join([str(x) for x in segment_ids]))
        logging.info("paragraph_mask: %s", " ".join(
            [str(x) for x in paragraph_mask]))
        logging.info("class_index: %d", class_index)

        if is_training and span_is_impossible:
          logging.info("impossible example span")

        if is_training and not span_is_impossible:
          pieces = [
              tokenizer.sp_model.IdToPiece(token)
              for token in tokens[start_position:(end_position + 1)]
          ]
          answer_text = tokenizer.sp_model.DecodePieces(pieces)
          logging.info("start_position: %d", (start_position))
          logging.info("end_position: %d", (end_position))
          logging.info("answer: %s", (tokenization.printable_text(answer_text)))

          # With multi processing, the example_index is actually the index
          # within the current process therefore we use example_index=None
          # to avoid being used in the future.
          # The current code does not use example_index of training data.
      if is_training:
        feat_example_index = None
      else:
        feat_example_index = example_index

      feature = InputFeatures(
          unique_id=unique_id,
          example_index=feat_example_index,
          doc_span_index=doc_span_index,
          tok_start_to_orig_index=cur_tok_start_to_orig_index,
          tok_end_to_orig_index=cur_tok_end_to_orig_index,
          token_is_max_context=token_is_max_context,
          tokens=[tokenizer.sp_model.IdToPiece(x) for x in tokens],
          input_ids=input_ids,
          input_mask=input_mask,
          paragraph_mask=paragraph_mask,
          segment_ids=segment_ids,
          paragraph_len=paragraph_len,
          class_index=class_index,
          start_position=start_position,
          end_position=end_position,
          is_impossible=span_is_impossible)

      # Run callback
      if is_training:
        output_fn(feature)
      else:
        output_fn(feature, is_padding=False)

      unique_id += 1
      if span_is_impossible:
        cnt_neg += 1
      else:
        cnt_pos += 1

  if not is_training and feature:
    assert batch_size
    num_padding = 0
    num_examples = unique_id - base_id
    if unique_id % batch_size != 0:
      num_padding = batch_size - (num_examples % batch_size)
    dummy_feature = copy.deepcopy(feature)
    for _ in range(num_padding):
      dummy_feature.unique_id = unique_id

      # Run callback
      output_fn(feature, is_padding=True)
      unique_id += 1

  logging.info("Total number of instances: %d = pos %d neg %d",
               cnt_pos + cnt_neg, cnt_pos, cnt_neg)
  return unique_id - base_id