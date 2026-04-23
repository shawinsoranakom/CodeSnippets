def _masking_ngrams(grams, max_ngram_size, max_masked_tokens, rng):
  """Create a list of masking {1, ..., n}-grams from a list of one-grams.

  This is an extension of 'whole word masking' to mask multiple, contiguous
  words such as (e.g., "the red boat").

  Each input gram represents the token indices of a single word,
     words:  ["the", "red", "boat"]
     tokens: ["the", "red", "boa", "##t"]
     grams:  [(0,1), (1,2), (2,4)]

  For a `max_ngram_size` of three, possible outputs masks include:
    1-grams: (0,1), (1,2), (2,4)
    2-grams: (0,2), (1,4)
    3-grams; (0,4)

  Output masks will not overlap and contain less than `max_masked_tokens` total
  tokens.  E.g., for the example above with `max_masked_tokens` as three,
  valid outputs are,
       [(0,1), (1,2)]  # "the", "red" covering two tokens
       [(1,2), (2,4)]  # "red", "boa", "##t" covering three tokens

  The length of the selected n-gram follows a zipf weighting to
  favor shorter n-gram sizes (weight(1)=1, weight(2)=1/2, weight(3)=1/3, ...).

  Args:
    grams: List of one-grams.
    max_ngram_size: Maximum number of contiguous one-grams combined to create
      an n-gram.
    max_masked_tokens: Maximum total number of tokens to be masked.
    rng: `random.Random` generator.

  Returns:
    A list of n-grams to be used as masks.
  """
  if not grams:
    return None

  grams = sorted(grams)
  num_tokens = grams[-1].end

  # Ensure our grams are valid (i.e., they don't overlap).
  for a, b in _window(grams, 2):
    if a.end > b.begin:
      raise ValueError("overlapping grams: {}".format(grams))

  # Build map from n-gram length to list of n-grams.
  ngrams = {i: [] for i in range(1, max_ngram_size+1)}
  for gram_size in range(1, max_ngram_size+1):
    for g in _window(grams, gram_size):
      if _contiguous(g):
        # Add an n-gram which spans these one-grams.
        ngrams[gram_size].append(_Gram(g[0].begin, g[-1].end))

  # Shuffle each list of n-grams.
  for v in ngrams.values():
    rng.shuffle(v)

  # Create the weighting for n-gram length selection.
  # Stored cumulatively for `random.choices` below.
  cummulative_weights = list(
      itertools.accumulate([1./n for n in range(1, max_ngram_size+1)]))

  output_ngrams = []
  # Keep a bitmask of which tokens have been masked.
  masked_tokens = [False] * num_tokens
  # Loop until we have enough masked tokens or there are no more candidate
  # n-grams of any length.
  # Each code path should ensure one or more elements from `ngrams` are removed
  # to guarantee this loop terminates.
  while (sum(masked_tokens) < max_masked_tokens and
         sum(len(s) for s in ngrams.values())):
    # Pick an n-gram size based on our weights.
    sz = random.choices(range(1, max_ngram_size+1),
                        cum_weights=cummulative_weights)[0]

    # Ensure this size doesn't result in too many masked tokens.
    # E.g., a two-gram contains _at least_ two tokens.
    if sum(masked_tokens) + sz > max_masked_tokens:
      # All n-grams of this length are too long and can be removed from
      # consideration.
      ngrams[sz].clear()
      continue

    # All of the n-grams of this size have been used.
    if not ngrams[sz]:
      continue

    # Choose a random n-gram of the given size.
    gram = ngrams[sz].pop()
    num_gram_tokens = gram.end-gram.begin

    # Check if this would add too many tokens.
    if num_gram_tokens + sum(masked_tokens) > max_masked_tokens:
      continue

    # Check if any of the tokens in this gram have already been masked.
    if sum(masked_tokens[gram.begin:gram.end]):
      continue

    # Found a usable n-gram!  Mark its tokens as masked and add it to return.
    masked_tokens[gram.begin:gram.end] = [True] * (gram.end-gram.begin)
    output_ngrams.append(gram)
  return output_ngrams