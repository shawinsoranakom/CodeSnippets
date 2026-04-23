def get_instruction_source_311(code: types.CodeType, inst: Instruction) -> str:
    """
    Python 3.11+ only. Returns lines of source code (from code object `code`)
    corresponding to `inst`'s location data, and underlines relevant code to `inst`.

    Example: CALL on `g`:
    f(g(
      ^^
        h(x)))
        ^^^^^

    We need our own implementation in < 3.13 since `format_frame_summary` in
    Python's `traceback` module doesn't handle multi-line expressions
    (and their anchor extraction code is not completely correct).
    """
    if sys.version_info >= (3, 13):
        # multiline traceback implemented in 3.13+
        frame_summary = traceback.FrameSummary(
            code.co_filename,
            inst.positions.lineno,
            code.co_name,
            end_lineno=inst.positions.end_lineno,
            colno=inst.positions.col_offset,
            end_colno=inst.positions.end_col_offset,
        )
        result = traceback.format_list([frame_summary])[0]
        # remove first line containing filename info
        result = "\n".join(result.splitlines()[1:])
        # indent lines with original indentation
        orig_lines = [
            linecache.getline(code.co_filename, lineno).rstrip()
            for lineno in range(inst.positions.lineno, inst.positions.end_lineno + 1)
        ]
        orig_lines_dedent = textwrap.dedent("\n".join(orig_lines)).splitlines()
        indent_len = len(orig_lines[0]) - len(orig_lines_dedent[0])
        indent = orig_lines[0][:indent_len]
        result = textwrap.indent(textwrap.dedent(result), indent)
        return result

    assert hasattr(inst, "positions") and inst.positions is not None
    if inst.positions.lineno is None:
        return ""
    # The rstrip + "\n" pattern is used throughout this function to handle
    # linecache.getline errors. Error lines are treated as empty strings "", but we want
    # to treat them as blank lines "\n".
    first_line = linecache.getline(code.co_filename, inst.positions.lineno).rstrip()
    if inst.positions.end_lineno is None:
        return first_line
    if inst.positions.col_offset is None or inst.positions.end_col_offset is None:
        return first_line

    # character index of the start of the instruction
    start_offset = _fix_offset(first_line, inst.positions.col_offset)
    # character index of the end of the instruction
    # compute later since end may be a different line
    end_offset = None
    # expression corresponding to the instruction so we can get anchors
    segment = ""
    # underline markers to be printed - start with `~` marker and replace with `^` later
    markers = []

    # Compute segment and initial markers
    if inst.positions.end_lineno == inst.positions.lineno:
        end_offset = _fix_offset(first_line, inst.positions.end_col_offset)
        segment = first_line[start_offset:end_offset]
        markers.append(" " * start_offset + "~" * (end_offset - start_offset))
    else:
        segment = first_line[start_offset:] + "\n"
        markers.append(" " * start_offset + "~" * (len(first_line) - start_offset))
        last_line = linecache.getline(
            code.co_filename, inst.positions.end_lineno
        ).rstrip()
        end_offset = _fix_offset(last_line, inst.positions.end_col_offset)
        for lineno in range(inst.positions.lineno + 1, inst.positions.end_lineno):
            line = linecache.getline(code.co_filename, lineno).rstrip()
            segment += line + "\n"
            # don't underline leading spaces
            num_spaces = len(line) - len(line.lstrip())
            markers.append(" " * num_spaces + "~" * (len(line) - num_spaces))
        segment += last_line[:end_offset]
        num_spaces = len(last_line) - len(last_line.lstrip())
        markers.append(" " * num_spaces + "~" * (end_offset - num_spaces))

    anchors: _Anchors | None = None
    try:
        anchors = _extract_anchors_from_expr(segment)
    except AssertionError:
        pass

    # replace `~` markers with `^` where necessary
    if anchors is None:
        markers = [marker.replace("~", "^") for marker in markers]
    else:
        # make markers mutable
        mutable_markers: list[list[str]] = [list(marker) for marker in markers]

        # anchor positions do not take start_offset into account
        if anchors.left_end_lineno == 0:
            anchors.left_end_offset += start_offset
        if anchors.right_start_lineno == 0:
            anchors.right_start_offset += start_offset

        # Turn `~`` markers between anchors to `^`
        for lineno in range(len(markers)):
            for col in range(len(mutable_markers[lineno])):
                if lineno < anchors.left_end_lineno:
                    continue
                if lineno == anchors.left_end_lineno and col < anchors.left_end_offset:
                    continue
                if (
                    lineno == anchors.right_start_lineno
                    and col >= anchors.right_start_offset
                ):
                    continue
                if lineno > anchors.right_start_lineno:
                    continue
                if mutable_markers[lineno][col] == "~":
                    mutable_markers[lineno][col] = "^"

        # make markers into strings again
        markers = ["".join(marker) for marker in mutable_markers]

    result = ""
    for i in range(len(markers)):
        result += (
            linecache.getline(code.co_filename, inst.positions.lineno + i).rstrip()
            + "\n"
        )
        result += markers[i] + "\n"
    return result