def encode_pieces(sp_model, text, sample=False):
  """Segements text into pieces.

  This method is used together with sentence piece tokenizer and is forked from:
  https://github.com/google-research/google-research/blob/e1f6fa00/albert/tokenization.py


  Args:
    sp_model: A spm.SentencePieceProcessor object.
    text: The input text to be segemented.
    sample: Whether to randomly sample a segmentation output or return a
      deterministic one.

  Returns:
    A list of token pieces.
  """
  if six.PY2 and isinstance(text, six.text_type):
    text = six.ensure_binary(text, "utf-8")

  if not sample:
    pieces = sp_model.EncodeAsPieces(text)
  else:
    pieces = sp_model.SampleEncodeAsPieces(text, 64, 0.1)
  new_pieces = []
  for piece in pieces:
    piece = printable_text(piece)
    if len(piece) > 1 and piece[-1] == "," and piece[-2].isdigit():
      cur_pieces = sp_model.EncodeAsPieces(piece[:-1].replace(
          SPIECE_UNDERLINE, ""))
      if piece[0] != SPIECE_UNDERLINE and cur_pieces[0][0] == SPIECE_UNDERLINE:
        if len(cur_pieces[0]) == 1:
          cur_pieces = cur_pieces[1:]
        else:
          cur_pieces[0] = cur_pieces[0][1:]
      cur_pieces.append(piece[-1])
      new_pieces.extend(cur_pieces)
    else:
      new_pieces.append(piece)

  return new_pieces