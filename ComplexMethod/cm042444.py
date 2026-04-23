def _parse_quoted(s: str) -> str:
  """Parse a PO-format quoted string."""
  s = s.strip()
  if not (s.startswith('"') and s.endswith('"')):
    raise ValueError(f"Expected quoted string: {s!r}")
  s = s[1:-1]
  result: list[str] = []
  i = 0
  while i < len(s):
    if s[i] == '\\' and i + 1 < len(s):
      c = s[i + 1]
      if c == 'n':
        result.append('\n')
      elif c == 't':
        result.append('\t')
      elif c == '"':
        result.append('"')
      elif c == '\\':
        result.append('\\')
      else:
        result.append(s[i:i + 2])
      i += 2
    else:
      result.append(s[i])
      i += 1
  return ''.join(result)