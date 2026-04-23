def preprocess_text(inputs, lower=False, remove_space=True, keep_accents=False):
  """Preprocesses texts."""
  if remove_space:
    outputs = ' '.join(inputs.strip().split())
  else:
    outputs = inputs

  outputs = outputs.replace('``', '"').replace("''", '"')

  if six.PY2 and isinstance(outputs, str):
    outputs = outputs.decode('utf-8')

  if not keep_accents:
    outputs = unicodedata.normalize('NFKD', outputs)
    outputs = ''.join([c for c in outputs if not unicodedata.combining(c)])
  if lower:
    outputs = outputs.lower()

  return outputs