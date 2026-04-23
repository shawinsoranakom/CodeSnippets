def reverse_forbidden_text_careful_brace(
    text, mask, pattern, flags=0, forbid_wrapper=True
):
    """
    Move area out of preserve area (make text editable for GPT)
    count the number of the braces so as to catch complete text area.
    e.g.
    \caption{blablablablabla\texbf{blablabla}blablabla.}
    """
    pattern_compile = re.compile(pattern, flags)
    for res in pattern_compile.finditer(text):
        brace_level = 0
        p = begin = end = res.regs[1][0]
        for _ in range(1024 * 16):
            if text[p] == "}" and brace_level == 0:
                break
            elif text[p] == "}":
                brace_level -= 1
            elif text[p] == "{":
                brace_level += 1
            p += 1
        end = p
        mask[begin:end] = TRANSFORM
        if forbid_wrapper:
            mask[res.regs[0][0] : begin] = PRESERVE
            mask[end : res.regs[0][1]] = PRESERVE
    return text, mask