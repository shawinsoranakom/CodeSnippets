def _split_bpp(bpp: bytes) -> list[bytes]:
  """Split a BoundProfilePackage into APDU chunks per SGP.22 §5.7.6."""
  root_value = None
  for tag, value, start, end in iter_tlv(bpp, with_positions=True):
    if tag == TAG_BPP:
      root_value = value
      val_start = start + _parse_tlv_header_len(bpp[start:end])
      break
  if root_value is None:
    raise RuntimeError("Invalid BoundProfilePackage")

  chunks: list[bytes] = []
  for tag, value, start, end in iter_tlv(root_value, with_positions=True):
    if tag == TAG_BPP_COMMAND:
      chunks.append(bpp[0 : val_start + end])
    elif tag in (0xA0, 0xA2):
      chunks.append(bpp[val_start + start : val_start + end])
    elif tag in (0xA1, 0xA3):
      hdr_len = _parse_tlv_header_len(root_value[start:end])
      chunks.append(bpp[val_start + start : val_start + start + hdr_len])
      for _, _, cs, ce in iter_tlv(value, with_positions=True):
        chunks.append(value[cs:ce])
  return chunks