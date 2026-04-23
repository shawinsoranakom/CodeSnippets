def create_masked_lm_predictions(tokens, masked_lm_prob,
                                 max_predictions_per_seq, vocab_words, rng,
                                 do_whole_word_mask,
                                 max_ngram_size=None):
  """Creates the predictions for the masked LM objective."""
  if do_whole_word_mask:
    grams = _tokens_to_grams(tokens)
  else:
    # Here we consider each token to be a word to allow for sub-word masking.
    if max_ngram_size:
      raise ValueError("cannot use ngram masking without whole word masking")
    grams = [_Gram(i, i+1) for i in range(0, len(tokens))
             if tokens[i] not in ["[CLS]", "[SEP]"]]

  num_to_predict = min(max_predictions_per_seq,
                       max(1, int(round(len(tokens) * masked_lm_prob))))
  # Generate masks.  If `max_ngram_size` in [0, None] it means we're doing
  # whole word masking or token level masking.  Both of these can be treated
  # as the `max_ngram_size=1` case.
  masked_grams = _masking_ngrams(grams, max_ngram_size or 1,
                                 num_to_predict, rng)
  masked_lms = []
  output_tokens = list(tokens)
  for gram in masked_grams:
    # 80% of the time, replace all n-gram tokens with [MASK]
    if rng.random() < 0.8:
      replacement_action = lambda idx: "[MASK]"
    else:
      # 10% of the time, keep all the original n-gram tokens.
      if rng.random() < 0.5:
        replacement_action = lambda idx: tokens[idx]
      # 10% of the time, replace each n-gram token with a random word.
      else:
        replacement_action = lambda idx: rng.choice(vocab_words)

    for idx in range(gram.begin, gram.end):
      output_tokens[idx] = replacement_action(idx)
      masked_lms.append(MaskedLmInstance(index=idx, label=tokens[idx]))

  assert len(masked_lms) <= num_to_predict
  masked_lms = sorted(masked_lms, key=lambda x: x.index)

  masked_lm_positions = []
  masked_lm_labels = []
  for p in masked_lms:
    masked_lm_positions.append(p.index)
    masked_lm_labels.append(p.label)

  return (output_tokens, masked_lm_positions, masked_lm_labels)