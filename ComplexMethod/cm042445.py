def load_translations(path) -> tuple[dict[str, str], dict[str, list[str]]]:
  """Parse a .po file and return (translations, plurals) dicts.

  translations: msgid -> msgstr
  plurals: msgid -> [msgstr[0], msgstr[1], ...]
  """
  with path.open(encoding='utf-8') as f:
    lines = f.readlines()

  translations: dict[str, str] = {}
  plurals: dict[str, list[str]] = {}

  # Parser state
  msgid = msgid_plural = msgstr = ""
  msgstr_plurals: dict[int, str] = {}
  field: str | None = None
  plural_idx = 0

  def finish():
    nonlocal msgid, msgid_plural, msgstr, msgstr_plurals, field
    if msgid:  # skip header (empty msgid)
      if msgid_plural:
        max_idx = max(msgstr_plurals.keys()) if msgstr_plurals else 0
        plurals[msgid] = [msgstr_plurals.get(i, '') for i in range(max_idx + 1)]
      else:
        translations[msgid] = msgstr
    msgid = msgid_plural = msgstr = ""
    msgstr_plurals = {}
    field = None

  for raw in lines:
    line = raw.strip()

    if not line:
      finish()
      continue

    if line.startswith('#'):
      continue

    if line.startswith('msgid_plural '):
      msgid_plural = _parse_quoted(line[len('msgid_plural '):])
      field = 'msgid_plural'
      continue

    if line.startswith('msgid '):
      msgid = _parse_quoted(line[len('msgid '):])
      field = 'msgid'
      continue

    m = re.match(r'msgstr\[(\d+)]\s+(.*)', line)
    if m:
      plural_idx = int(m.group(1))
      msgstr_plurals[plural_idx] = _parse_quoted(m.group(2))
      field = 'msgstr_plural'
      continue

    if line.startswith('msgstr '):
      msgstr = _parse_quoted(line[len('msgstr '):])
      field = 'msgstr'
      continue

    if line.startswith('"'):
      val = _parse_quoted(line)
      if field == 'msgid':
        msgid += val
      elif field == 'msgid_plural':
        msgid_plural += val
      elif field == 'msgstr':
        msgstr += val
      elif field == 'msgstr_plural':
        msgstr_plurals[plural_idx] += val

  finish()
  return translations, plurals