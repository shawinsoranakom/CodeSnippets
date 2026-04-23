def _derive_assistant_prefix_by_render(chat_template, is_sharegpt = False):
    """Return the assistant-turn prefix the template emits, derived by
    rendering two dialogs that differ only in assistant content: the common
    prefix of their tails (after the base [user]-only render) is what the
    template emits for an assistant turn. None if any guard fails.

    Works for Llama-3 / Gemma / Phi-3 and other non-ChatML shapes; the
    template is its own ground truth.

    Known limitation: an `eos-on-non-last` pattern (turn-end sentinel only
    emitted for non-last messages) would produce a consistent but wrong
    prefix that `_validate_patched_template` can't catch. No real-world
    template is known to use this.
    """
    try:
        from jinja2.sandbox import SandboxedEnvironment
    except Exception:
        return None

    if is_sharegpt:
        base_msgs = [{"from": "human", "value": "Hi"}]
        sent_a_msgs = base_msgs + [{"from": "gpt", "value": _RENDER_DIFF_SENTINEL_A}]
        sent_b_msgs = base_msgs + [{"from": "gpt", "value": _RENDER_DIFF_SENTINEL_B}]
        # User-role cross-check (Guard C below).
        sent_c_msgs = base_msgs + [{"from": "human", "value": _RENDER_DIFF_SENTINEL_C}]
    else:
        base_msgs = [{"role": "user", "content": "Hi"}]
        sent_a_msgs = base_msgs + [
            {"role": "assistant", "content": _RENDER_DIFF_SENTINEL_A}
        ]
        sent_b_msgs = base_msgs + [
            {"role": "assistant", "content": _RENDER_DIFF_SENTINEL_B}
        ]
        sent_c_msgs = base_msgs + [{"role": "user", "content": _RENDER_DIFF_SENTINEL_C}]

    # Strip trailing whitespace/comments after the last endfor/endif: they
    # appear after the message loop and would break Guard A. The splice in
    # `_fix_chat_template` drops them too.
    probe_template = chat_template
    end = _find_end_position(chat_template)
    if end is not None:
        after = chat_template[end["end"] :]
        if _RE_JINJA_COMMENT.sub("", after).strip() == "":
            probe_template = chat_template[: end["end"]]

    # Sandboxed: probe renders at load time, before user calls
    # apply_chat_template. SandboxedEnvironment blocks attribute-chain exploits.
    try:
        env = SandboxedEnvironment(
            autoescape = False,
            keep_trailing_newline = True,
        )
        tmpl = env.from_string(probe_template)
        out_base = tmpl.render(messages = base_msgs, add_generation_prompt = False)
        out_a = tmpl.render(messages = sent_a_msgs, add_generation_prompt = False)
        out_b = tmpl.render(messages = sent_b_msgs, add_generation_prompt = False)
    except Exception:
        return None

    # Best-effort: alternation-enforcing templates (e.g. Gemma's
    # raise_exception) fail on [user, user]; that's a positive signal
    # for Guard C, not a probe failure.
    out_user_c = None
    try:
        out_user_c = tmpl.render(messages = sent_c_msgs, add_generation_prompt = False)
    except Exception:
        pass

    # Guard A: assistant renders extend base (no reordering).
    if not (out_a.startswith(out_base) and out_b.startswith(out_base)):
        return None

    tail_a = out_a[len(out_base) :]
    tail_b = out_b[len(out_base) :]
    if not tail_a or not tail_b:
        return None

    prefix = os.path.commonprefix([tail_a, tail_b])

    # Guard B: divergence is exactly at the content-insertion site.
    if not (
        tail_a[len(prefix) :].startswith(_RENDER_DIFF_SENTINEL_A)
        and tail_b[len(prefix) :].startswith(_RENDER_DIFF_SENTINEL_B)
    ):
        return None

    # Guard C: reject if a [user, user] render also emits the same prefix
    # (role-insensitive template, e.g. `{% set greeting='Hi' %}...`).
    if out_user_c is not None and out_user_c.startswith(out_base):
        tail_c = out_user_c[len(out_base) :]
        if tail_c.startswith(prefix) and prefix != "":
            return None

    if not prefix:
        return None

    return prefix