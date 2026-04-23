def _propagate_fixes_to_modular(
    generated_file: str,
    decorated_items: list,
    overwrite: bool = False,
) -> bool:
    """After fixing docstrings in a generated file, propagate the same fixes to the
    corresponding modular_*.py source file.

    For each @auto_docstring item processed in *generated_file*, we look for the
    same class/method (by name) in the modular source.  If the modular item has an
    *explicit* docstring we sync it using the *generated* file as the ground truth:

    - Arg descriptions come from the generated docstring (which was just fixed/reordered).
      Descriptions present in the modular docstring take priority over the generated ones
      (modular is the source), but args that exist in the generated docstring and were
      missing from the modular (e.g. stripped by a previous bug) are restored.
    - The Example/Returns section is taken from the modular docstring (modular-specific).
    - Arg order follows gen_item.args (the generated file's annotation order).

    If the modular item has *no* docstring it was inherited and we leave it untouched.

    Returns True when the modular file was (or would be) changed.
    """
    modular_file = _find_corresponding_modular_file(generated_file)
    if not modular_file:
        return False

    try:
        with open(modular_file, encoding="utf-8") as f:
            modular_content = f.read()
        modular_tree = ast.parse(modular_content)
        with open(generated_file, encoding="utf-8") as f:
            generated_content = f.read()
    except (OSError, SyntaxError):
        return False

    modular_lines = modular_content.split("\n")
    gen_lines = generated_content.split("\n")

    # Build a lookup: (class_name_or_None, item_name) -> (method_node, class_node_or_None)
    lookup: dict[tuple, tuple] = {}
    for node in modular_tree.body:
        if isinstance(node, ast.ClassDef):
            lookup[(None, node.name)] = (node, None)
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lookup[(node.name, child.name)] = (child, node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lookup[(None, node.name)] = (node, None)

    # Collect (docstring_start_0based, docstring_end_0based, new_lines) for each fix
    fixes: list[tuple[int, int, list[str]]] = []

    for gen_item in decorated_items:
        key = (gen_item.class_name, gen_item.name)
        entry = lookup.get(key)
        if entry is None:
            continue

        mod_node, _mod_class_node = entry

        # Find the "active" node containing the docstring
        # For class items with __init__: the docstring lives in __init__
        # For config classes (no __init__):  the docstring lives at class-body level
        # For function items: the node itself carries the docstring
        if gen_item.kind == "class" and gen_item.has_init:
            active_node = next(
                (m for m in mod_node.body if isinstance(m, ast.FunctionDef) and m.name == "__init__"),
                None,
            )
            if active_node is None:
                continue
        elif gen_item.kind == "class":
            active_node = mod_node
        else:
            active_node = mod_node

        # Skip if the modular item has no explicit docstring – it was inherited
        if not _node_has_docstring(active_node):
            continue

        # Locate the docstring in modular_lines (0-based)
        body_start_1based = active_node.body[0].lineno
        sig_end_0based = body_start_1based - 1  # 0-based index of the docstring line
        if sig_end_0based >= len(modular_lines):
            continue
        if '"""' not in modular_lines[sig_end_0based]:
            continue
        doc_end_0based = _find_docstring_end_line(modular_lines, sig_end_0based)
        if doc_end_0based is None:
            continue

        # Parse the modular docstring to get its current arg descriptions and remaining section
        mod_doc_raw = _normalize_docstring_code_fences("\n".join(modular_lines[sig_end_0based : doc_end_0based + 1]))
        mod_args_dict, mod_remaining = parse_docstring(mod_doc_raw)

        # Parse the generated docstring to get the authoritative (fixed) arg descriptions.
        # gen_item.body_start_line is 1-based and points to the first line of the body
        # (which is always the docstring for @auto_docstring items).
        gen_doc_start_0 = gen_item.body_start_line - 1
        gen_doc_end_0 = _find_docstring_end_line(gen_lines, gen_doc_start_0)
        if gen_doc_end_0 is not None and '"""' in gen_lines[gen_doc_start_0]:
            gen_doc_raw = _normalize_docstring_code_fences("\n".join(gen_lines[gen_doc_start_0 : gen_doc_end_0 + 1]))
            gen_args_dict, gen_remaining = parse_docstring(gen_doc_raw)
        else:
            gen_args_dict, gen_remaining = {}, ""

        # Merge: generated docstring is the base (has all args, already fixed/reordered),
        # modular descriptions take priority where both have the same arg.
        merged = dict(gen_args_dict)
        merged.update(mod_args_dict)

        # Order merged args by gen_item.args (generated annotation order).
        # Extra args that are only in modular (not yet in generated) are appended at the end.
        ordered: dict = {}
        for arg in gen_item.args:
            if arg in merged:
                ordered[arg] = merged[arg]
        for arg, info in mod_args_dict.items():
            if arg not in ordered:
                ordered[arg] = info

        # Prefer the modular's remaining section (its Example/Returns are modular-specific).
        # Fall back to the generated remaining only when the modular has none.
        remaining = mod_remaining or gen_remaining

        # Build the new docstring string (mirrors generate_new_docstring_for_signature logic)
        if not ordered and not remaining:
            continue
        new_doc = 'r"""\n'
        for arg, info in ordered.items():
            additional_info = info.get("additional_info") or ""
            description = info.get("description", "")
            if description.endswith('"""'):
                description = "\n".join(description.split("\n")[:-1])
            new_doc += f"{arg} ({info['type']}{additional_info}):{description}\n"
        close_doc = True
        if remaining:
            if remaining.endswith('"""'):
                # remaining already contains the closing """; don't add it separately
                close_doc = False
            end_remaining = "\n" if close_doc else ""
            new_doc += f"{set_min_indent(remaining, 0)}{end_remaining}"
        if close_doc:
            new_doc += '"""'

        # Indent to match the modular docstring's own indentation
        raw_doc_line = modular_lines[sig_end_0based]
        output_indent = len(raw_doc_line) - len(raw_doc_line.lstrip())
        new_docstring = set_min_indent(new_doc, output_indent)

        old_lines = modular_lines[sig_end_0based : doc_end_0based + 1]
        new_lines = new_docstring.split("\n")
        if old_lines == new_lines:
            continue

        fixes.append((sig_end_0based, doc_end_0based, new_lines))

    if not fixes:
        return False

    # Apply fixes in reverse line order so earlier line numbers stay valid
    fixes.sort(key=lambda x: x[0], reverse=True)
    for start, end, new_lines in fixes:
        modular_lines[start : end + 1] = new_lines

    if overwrite:
        with open(modular_file, "w", encoding="utf-8") as f:
            f.write("\n".join(modular_lines))
    return True