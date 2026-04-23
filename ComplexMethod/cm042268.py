def extract_strings(files: list[str], basedir: str) -> list[POEntry]:
  """Extract tr/trn/tr_noop calls from Python source files."""
  seen: dict[str, POEntry] = {}

  for filepath in files:
    full = os.path.join(basedir, filepath)
    with open(full, encoding='utf-8') as f:
      source = f.read()
    try:
      tree = ast.parse(source, filename=filepath)
    except SyntaxError:
      continue

    for node in ast.walk(tree):
      if not isinstance(node, ast.Call):
        continue

      func = node.func
      if isinstance(func, ast.Name):
        name = func.id
      elif isinstance(func, ast.Attribute):
        name = func.attr
      else:
        continue

      if name not in ('tr', 'trn', 'tr_noop'):
        continue

      ref = f'{filepath}:{node.lineno}'
      is_flagged = name in ('tr', 'trn')

      if name in ('tr', 'tr_noop'):
        if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
          continue
        msgid = node.args[0].value
        if msgid in seen:
          if ref not in seen[msgid].source_refs:
            seen[msgid].source_refs.append(ref)
        else:
          flags = ['python-format'] if is_flagged else []
          seen[msgid] = POEntry(msgid=msgid, source_refs=[ref], flags=flags)

      elif name == 'trn':
        if len(node.args) < 2:
          continue
        a1, a2 = node.args[0], node.args[1]
        if not (isinstance(a1, ast.Constant) and isinstance(a1.value, str)):
          continue
        if not (isinstance(a2, ast.Constant) and isinstance(a2.value, str)):
          continue
        msgid, msgid_plural = a1.value, a2.value
        if msgid in seen:
          if ref not in seen[msgid].source_refs:
            seen[msgid].source_refs.append(ref)
        else:
          flags = ['python-format'] if is_flagged else []
          seen[msgid] = POEntry(
            msgid=msgid, msgid_plural=msgid_plural,
            source_refs=[ref], flags=flags,
            msgstr_plural={0: '', 1: ''},
          )

  return list(seen.values())