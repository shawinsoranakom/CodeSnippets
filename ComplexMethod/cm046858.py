def _fix_chat_template(chat_template, is_sharegpt = False):
    # Fast path: already has an {% if add_generation_prompt %} block, nothing
    # to do. This catches cases the old string-based check would miss (e.g.
    # templates that use {%- if add_generation_prompt -%} with both-side dash,
    # or that sneak the block into a nested If/For).
    if _has_add_generation_prompt_block(chat_template):
        return chat_template

    end = _find_end_position(chat_template)
    if end is None:
        return chat_template

    after_endfor = chat_template[end["end"] :]
    dash_l = "-" if end["dash_left"] else ""
    dash_r = "-" if end["dash_right"] else ""
    open_tag = lambda body: "{%" + dash_l + " " + body + " " + dash_r + "%}"

    # Case 1 (pre-existing base case): template ends with a single trailing
    # {{ expr }} that is the generation prefix. Wrap it in an
    # {% if add_generation_prompt %} ... {% endif %}.
    if (
        "{%" + dash_l + " if" not in after_endfor
        and "{%" + dash_l + " set " not in after_endfor
        and after_endfor.startswith("{{")
        and after_endfor.endswith("}}")
        and after_endfor.count("{{") == 1
        and after_endfor.count("}}") == 1
    ):
        wrapped = (
            open_tag("if add_generation_prompt") + after_endfor + open_tag("endif")
        )
        return chat_template[: end["end"]] + wrapped

    # Case 2 (GH#4150): template ends at {% endfor %} with only whitespace
    # or comments left. Inject an {% if add_generation_prompt %} block with
    # the assistant prefix derived by render-diff. The top-level-For gate
    # keeps us out of outer-If wrappers (e.g. Qwen3-Guard).
    if _RE_JINJA_COMMENT.sub(
        "", after_endfor
    ).strip() == "" and _template_ends_with_toplevel_for(chat_template):
        # No redundant "agp not in scrubbed" check: the fast path already
        # confirmed no *positive* block, and a mere reference (header
        # guard) should still get repaired.
        assistant_prefix = _derive_assistant_prefix_by_render(
            chat_template, is_sharegpt
        )
        # Dual-probe: dict/list callers don't know the shape up front.
        if assistant_prefix is None and not is_sharegpt:
            assistant_prefix = _derive_assistant_prefix_by_render(
                chat_template, is_sharegpt = True
            )
        if assistant_prefix is None:
            return chat_template
        # Escape for a double-quoted Jinja string literal.
        escaped = (
            assistant_prefix.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )
        generation_block = (
            open_tag("if add_generation_prompt")
            + '{{ "'
            + escaped
            + '" }}'
            + open_tag("endif")
        )
        return chat_template[: end["end"]] + generation_block

    return chat_template