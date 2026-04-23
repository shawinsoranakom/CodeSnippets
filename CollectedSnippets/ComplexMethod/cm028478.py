def encode_pieces(sp_model, text, return_unicode=True, sample=False):
  """Encodes pieces."""
  # return_unicode is used only for py2

  if six.PY2 and isinstance(text, unicode):  # pylint: disable=undefined-variable
    text = text.encode('utf-8')

  if not sample:
    pieces = sp_model.EncodeAsPieces(text)
  else:
    pieces = sp_model.SampleEncodeAsPieces(text, 64, 0.1)
  new_pieces = []
  for piece in pieces:
    if len(piece) > 1 and piece[-1] == ',' and piece[-2].isdigit():
      cur_pieces = sp_model.EncodeAsPieces(piece[:-1].replace(
          SPIECE_UNDERLINE, ''))
      if piece[0] != SPIECE_UNDERLINE and cur_pieces[0][0] == SPIECE_UNDERLINE:
        if len(cur_pieces[0]) == 1:
          cur_pieces = cur_pieces[1:]
        else:
          cur_pieces[0] = cur_pieces[0][1:]
      cur_pieces.append(piece[-1])
      new_pieces.extend(cur_pieces)
    else:
      new_pieces.append(piece)

  # note(zhiliny): convert back to unicode for py2
  if six.PY2 and return_unicode:
    ret_pieces = []
    for piece in new_pieces:
      if isinstance(piece, str):
        piece = piece.decode('utf-8')
      ret_pieces.append(piece)
    new_pieces = ret_pieces

  return new_pieces