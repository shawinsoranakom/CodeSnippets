def _replace(self, parent: ET.Element, glossary_href: str, index: int | None = None) -> int:
    child = None if index is None else parent[index]
    text = parent.text if child is None else child.tail
    pieces = self._pieces(text or "", glossary_href)
    if not pieces:
      return -1 if index is None else index

    if child is None:
      parent.text = pieces[0] if isinstance(pieces[0], str) else ""
      # Insert replacements for parent.text before the first existing child.
      insert_at = -1
    else:
      assert index is not None
      child.tail = pieces[0] if isinstance(pieces[0], str) else ""
      insert_at = index

    start = 1 if isinstance(pieces[0], str) else 0
    previous = child

    for piece in pieces[start:]:
      if isinstance(piece, str):
        previous.tail = (previous.tail or "") + piece
        continue

      insert_at += 1
      parent.insert(insert_at, piece)
      previous = piece

    return insert_at