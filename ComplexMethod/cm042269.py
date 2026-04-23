def test_translation_placeholders_are_preserved(po_path: Path):
  _, entries = parse_po(po_path)
  language = po_path.stem.removeprefix("app_")

  for entry in entries:
    source_placeholders = extract_placeholders(entry.msgid)

    if entry.is_plural:
      plural_placeholders = extract_placeholders(entry.msgid_plural)
      message = (
        f"{language}: source plural placeholders do not match singular for "
        + f"{entry.msgid!r}: {source_placeholders} vs {plural_placeholders}"
      )
      assert plural_placeholders == source_placeholders, message

      for idx, msgstr in sorted(entry.msgstr_plural.items()):
        if not msgstr:
          continue

        translated_placeholders = extract_placeholders(msgstr)
        message = (
          f"{language}: plural form {idx} changes placeholders for {entry.msgid!r}: "
          + f"expected {source_placeholders}, got {translated_placeholders}"
        )
        assert translated_placeholders == source_placeholders, message
    else:
      if not entry.msgstr:
        continue

      translated_placeholders = extract_placeholders(entry.msgstr)
      message = (
        f"{language}: translation changes placeholders for {entry.msgid!r}: "
        + f"expected {source_placeholders}, got {translated_placeholders}"
      )
      assert translated_placeholders == source_placeholders, message