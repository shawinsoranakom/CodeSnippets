def check_absolute_targets_doc_role(file, lines, options=None):
    for paragraph_lno, paragraph in paragraphs(lines):
        for error in _DOC_CAPTURE_TARGET_RE.finditer(paragraph):
            target = error.group(1)
            # Skip absolute or intersphinx refs like "python:using/windows".
            if target.startswith("/") or ":" in target.split("/", 1)[0]:
                continue
            # Relative target, report as a violation.
            error_offset = paragraph[: error.start()].count("\n")
            yield (paragraph_lno + error_offset, target)