def get_tags(span_labels, length, encoding):
  """Converts a list of entities to token-label labels based on the provided
  encoding (e.g., BIOES).
  """

  tags = ['O' for _ in range(length)]
  for s, e, t in span_labels:
    for i in range(s, e + 1):
      tags[i] = 'I-' + t
    if 'E' in encoding:
      tags[e] = 'E-' + t
    if 'B' in encoding:
      tags[s] = 'B-' + t
    if 'S' in encoding and s == e:
      tags[s] = 'S-' + t
  return tags