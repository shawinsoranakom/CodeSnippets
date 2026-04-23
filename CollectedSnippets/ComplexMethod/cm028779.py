def preprocess_text(inputs, remove_space=True, lower=False):
  """Preprocesses data by removing extra space and normalize data.

  This method is used together with sentence piece tokenizer and is forked from:
  https://github.com/google-research/google-research/blob/e1f6fa00/albert/tokenization.py

  Args:
    inputs: The input text.
    remove_space: Whether to remove the extra space.
    lower: Whether to lowercase the text.

  Returns:
    The preprocessed text.

  """
  outputs = inputs
  if remove_space:
    outputs = " ".join(inputs.strip().split())

  if six.PY2 and isinstance(outputs, str):
    try:
      outputs = six.ensure_text(outputs, "utf-8")
    except UnicodeDecodeError:
      outputs = six.ensure_text(outputs, "latin-1")

  outputs = unicodedata.normalize("NFKD", outputs)
  outputs = "".join([c for c in outputs if not unicodedata.combining(c)])
  if lower:
    outputs = outputs.lower()

  return outputs