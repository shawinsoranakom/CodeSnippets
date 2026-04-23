def _int_format(field_type: IntType) -> str:
  if field_type.bits == 8:
    return 'b' if field_type.signed else 'B'
  endian = '>' if field_type.big_endian else '<'
  if field_type.bits == 16:
    code = 'h' if field_type.signed else 'H'
  elif field_type.bits == 32:
    code = 'i' if field_type.signed else 'I'
  else:
    raise ValueError(f"Unsupported integer size: {field_type.bits}")
  return f"{endian}{code}"