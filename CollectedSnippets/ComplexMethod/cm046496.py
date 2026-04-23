def test_flag_sits_inside_the_base_cmd_list():
    """Pin the flag's location so a future refactor can't accidentally
    move it into a branch that only fires on some code paths.

    We slice from ``cmd = [`` to the first ``]`` at the same indent.
    Using ``inspect.getsource`` means the function lives in its own
    string and there are no siblings to worry about, so a plain
    bracket search would also work -- anchoring on the trailing indent
    just keeps the slice from wandering into a later expression if the
    opening literal ever grows an in-line comment trailing it.
    """
    source = _load_model_source()
    start = source.find("cmd = [")
    assert start >= 0, "could not find the base cmd = [...] block"
    # Find the first line containing only ``]`` (possibly indented).
    # Works for any indentation style the formatter picks.
    rest = source[start:]
    end_rel = -1
    for line_start, line in _iter_lines_with_offset(rest):
        if line_start == 0:
            # Skip the opening ``cmd = [`` line itself.
            continue
        if line.strip() == "]":
            end_rel = line_start
            break
    assert end_rel > 0, "could not find end of cmd = [...] block"
    block = rest[:end_rel]
    assert '"--no-context-shift"' in block, (
        "--no-context-shift must be in the base cmd list, not in a "
        "conditional branch -- otherwise some code paths would still "
        "run with silent context shift enabled."
    )
    # Also pin that it is next to -c / --ctx so the grouping makes sense.
    assert '"-c"' in block
    assert '"--flash-attn"' in block