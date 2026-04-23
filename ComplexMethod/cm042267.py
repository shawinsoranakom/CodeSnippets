def write_po(path: str | Path, header: POEntry | None, entries: list[POEntry]) -> None:
  """Write a .po/.pot file."""
  with open(path, 'w', encoding='utf-8') as f:
    if header:
      for c in header.comments:
        f.write(c + '\n')
      f.write(f'msgid {_quote("")}\n')
      f.write(f'msgstr {_quote(header.msgstr)}\n\n')

    for entry in entries:
      for c in entry.comments:
        f.write(c + '\n')
      # Keep file-level context for translators, but drop line numbers to
      # avoid churning PO diffs on unrelated code edits.
      source_files = sorted({ref.rsplit(':', 1)[0] for ref in entry.source_refs})
      for ref in source_files:
        f.write(f'#: {ref}\n')
      # Runtime loading ignores gettext flags; omit them to reduce noise.
      f.write(f'msgid {_quote(entry.msgid)}\n')
      if entry.is_plural:
        f.write(f'msgid_plural {_quote(entry.msgid_plural)}\n')
        for idx in sorted(entry.msgstr_plural):
          f.write(f'msgstr[{idx}] {_quote(entry.msgstr_plural[idx])}\n')
      else:
        f.write(f'msgstr {_quote(entry.msgstr)}\n')
      f.write('\n')