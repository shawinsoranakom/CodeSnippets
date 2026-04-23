def _gen_new_subtoken_list(subtoken_counts,
                           min_count,
                           alphabet,
                           reserved_tokens=None):
  """Generate candidate subtokens ordered by count, and new max subtoken length.

  Add subtokens to the candiate list in order of length (longest subtokens
  first). When a subtoken is added, the counts of each of its prefixes are
  decreased. Prefixes that don't appear much outside the subtoken are not added
  to the candidate list.

  For example:
    subtoken being added to candidate list: 'translate'
    subtoken_counts: {'translate':10, 't':40, 'tr':16, 'tra':12, ...}
    min_count: 5

  When 'translate' is added, subtoken_counts is updated to:
    {'translate':0, 't':30, 'tr':6, 'tra': 2, ...}

  The subtoken 'tra' will not be added to the candidate list, because it appears
  twice (less than min_count) outside of 'translate'.

  Args:
    subtoken_counts: defaultdict mapping str subtokens to int counts
    min_count: int minumum count requirement for subtokens
    alphabet: set of characters. Each character is added to the subtoken list to
      guarantee that all tokens can be encoded.
    reserved_tokens: list of tokens that will be added to the beginning of the
      returned subtoken list.

  Returns:
    List of candidate subtokens in decreasing count order, and maximum subtoken
    length
  """
  if reserved_tokens is None:
    reserved_tokens = RESERVED_TOKENS

  # Create a list of (count, subtoken) for each candidate subtoken.
  subtoken_candidates = []

  # Use bucketted list to iterate through subtokens in order of length.
  # subtoken_buckets[i] = set(subtokens), where each subtoken has length i.
  subtoken_buckets = _filter_and_bucket_subtokens(subtoken_counts, min_count)
  max_subtoken_length = len(subtoken_buckets) - 1

  # Go through the list in reverse order to consider longer subtokens first.
  for subtoken_len in xrange(max_subtoken_length, 0, -1):
    for subtoken in subtoken_buckets[subtoken_len]:
      count = subtoken_counts[subtoken]

      # Possible if this subtoken is a prefix of another token.
      if count < min_count:
        continue

      # Ignore alphabet/reserved tokens, which will be added manually later.
      if subtoken not in alphabet and subtoken not in reserved_tokens:
        subtoken_candidates.append((count, subtoken))

      # Decrement count of the subtoken's prefixes (if a longer subtoken is
      # added, its prefixes lose priority to be added).
      for end in xrange(1, subtoken_len):
        subtoken_counts[subtoken[:end]] -= count

  # Add alphabet subtokens (guarantees that all strings are encodable).
  subtoken_candidates.extend((subtoken_counts.get(a, 0), a) for a in alphabet)

  # Order subtoken candidates by decreasing count.
  subtoken_list = [t for _, t in sorted(subtoken_candidates, reverse=True)]

  # Add reserved tokens to beginning of the list.
  subtoken_list = reserved_tokens + subtoken_list
  return subtoken_list, max_subtoken_length