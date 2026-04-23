def reshape(text):
    if not text:
        return ''

    output = []

    LETTER = 0
    FORM = 1
    NOT_SUPPORTED = -1

    for letter in text:
        if HARAKAT_RE.match(letter):
            pass
        elif letter not in LETTERS_ARABIC:
            output.append((letter, NOT_SUPPORTED))
        elif not output:  # first letter
            output.append((letter, ISOLATED))
        else:
            previous_letter = output[-1]
            if (
                previous_letter[FORM] == NOT_SUPPORTED or
                not connects_with_letter_before(letter, LETTERS_ARABIC) or
                not connects_with_letter_after(previous_letter[LETTER], LETTERS_ARABIC) or
                (previous_letter[FORM] == FINAL and not connects_with_letters_before_and_after(previous_letter[LETTER], LETTERS_ARABIC))
            ):
                output.append((letter, ISOLATED))
            elif previous_letter[FORM] == ISOLATED:
                output[-1] = (previous_letter[LETTER], INITIAL)
                output.append((letter, FINAL))
            # Otherwise, we will change the previous letter to connect
            # to the current letter
            else:
                output[-1] = (previous_letter[LETTER], MEDIAL)
                output.append((letter, FINAL))

        # Remove ZWJ if it's the second to last item as it won't be useful
        if len(output) > 1 and output[-2][LETTER] == ZWJ:
            output.pop(len(output) - 2)

    if output and output[-1][LETTER] == ZWJ:
        output.pop()

    # Clean text from Harakat to be able to find ligatures
    text = HARAKAT_RE.sub('', text)

    for match in LIGATURES_RE.finditer(text):
        group_index = next((
            i for i, group in enumerate(match.groups()) if group
        ), -1)
        forms = GROUP_INDEX_TO_LIGATURE_FORMs[group_index]
        a, b = match.span()
        a_form = output[a][FORM]
        b_form = output[b - 1][FORM]

        # +-----------+----------+---------+---------+----------+
        # | a   \   b | ISOLATED | INITIAL | MEDIAL  | FINAL    |
        # +-----------+----------+---------+---------+----------+
        # | ISOLATED  | ISOLATED | INITIAL | INITIAL | ISOLATED |
        # | INITIAL   | ISOLATED | INITIAL | INITIAL | ISOLATED |
        # | MEDIAL    | FINAL    | MEDIAL  | MEDIAL  | FINAL    |
        # | FINAL     | FINAL    | MEDIAL  | MEDIAL  | FINAL    |
        # +-----------+----------+---------+---------+----------+

        if a_form in (ISOLATED, INITIAL):
            if b_form in (ISOLATED, FINAL):
                ligature_form = ISOLATED
            else:
                ligature_form = INITIAL
        else:
            if b_form in (ISOLATED, FINAL):
                ligature_form = FINAL
            else:
                ligature_form = MEDIAL
        if not forms[ligature_form]:
            continue
        output[a] = (forms[ligature_form], NOT_SUPPORTED)
        output[a + 1:b] = repeat(('', NOT_SUPPORTED), b - 1 - a)

    result = []
    for o in output:
        if o[LETTER]:
            if o[FORM] == NOT_SUPPORTED or o[FORM] == UNSHAPED:
                result.append(o[LETTER])
            else:
                result.append(LETTERS_ARABIC[o[LETTER]][o[FORM]])

    return ''.join(result)