def parse_po(path: str | Path) -> tuple[POEntry | None, list[POEntry]]:
  """Parse a .po/.pot file. Returns (header_entry, entries)."""
  with open(path, encoding='utf-8') as f:
    lines = f.readlines()

  entries: list[POEntry] = []
  header: POEntry | None = None
  cur: POEntry | None = None
  cur_field: str | None = None
  plural_idx = 0

  def finish():
    nonlocal cur, header
    if cur is None:
      return
    if cur.msgid == "" and cur.msgstr:
      header = cur
    elif cur.msgid != "" or cur.is_plural:
      entries.append(cur)
    cur = None

  for raw in lines:
    line = raw.rstrip('\n')
    stripped = line.strip()

    if not stripped:
      finish()
      cur_field = None
      continue

    # Skip obsolete entries
    if stripped.startswith('#~'):
      continue

    if stripped.startswith('#'):
      if cur is None:
        cur = POEntry()
      if stripped.startswith('#:'):
        cur.source_refs.append(stripped[2:].strip())
      elif stripped.startswith('#,'):
        cur.flags.extend(f.strip() for f in stripped[2:].split(',') if f.strip())
      else:
        cur.comments.append(line)
      continue

    if stripped.startswith('msgid_plural '):
      if cur is None:
        cur = POEntry()
      cur.msgid_plural = _parse_quoted(stripped[len('msgid_plural '):])
      cur_field = 'msgid_plural'
      continue

    if stripped.startswith('msgid '):
      if cur is None:
        cur = POEntry()
      cur.msgid = _parse_quoted(stripped[len('msgid '):])
      cur_field = 'msgid'
      continue

    m = re.match(r'msgstr\[(\d+)]\s+(.*)', stripped)
    if m:
      plural_idx = int(m.group(1))
      cur.msgstr_plural[plural_idx] = _parse_quoted(m.group(2))
      cur_field = 'msgstr_plural'
      continue

    if stripped.startswith('msgstr '):
      cur.msgstr = _parse_quoted(stripped[len('msgstr '):])
      cur_field = 'msgstr'
      continue

    if stripped.startswith('"'):
      val = _parse_quoted(stripped)
      if cur_field == 'msgid':
        cur.msgid += val
      elif cur_field == 'msgid_plural':
        cur.msgid_plural += val
      elif cur_field == 'msgstr':
        cur.msgstr += val
      elif cur_field == 'msgstr_plural':
        cur.msgstr_plural[plural_idx] += val

  finish()
  return header, entries