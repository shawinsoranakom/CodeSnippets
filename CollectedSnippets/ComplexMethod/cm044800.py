def jyuping_to_initials_finals_tones(jyuping_syllables):
    initials_finals = []
    tones = []
    word2ph = []

    for syllable in jyuping_syllables:
        if syllable in punctuation:
            initials_finals.append(syllable)
            tones.append(0)
            word2ph.append(1)  # Add 1 for punctuation
        elif syllable == "_":
            initials_finals.append(syllable)
            tones.append(0)
            word2ph.append(1)  # Add 1 for underscore
        else:
            try:
                tone = int(syllable[-1])
                syllable_without_tone = syllable[:-1]
            except ValueError:
                tone = 0
                syllable_without_tone = syllable

            for initial in INITIALS:
                if syllable_without_tone.startswith(initial):
                    if syllable_without_tone.startswith("nga"):
                        initials_finals.extend(
                            [
                                syllable_without_tone[:2],
                                syllable_without_tone[2:] or syllable_without_tone[-1],
                            ]
                        )
                        # tones.extend([tone, tone])
                        tones.extend([-1, tone])
                        word2ph.append(2)
                    else:
                        final = syllable_without_tone[len(initial) :] or initial[-1]
                        initials_finals.extend([initial, final])
                        # tones.extend([tone, tone])
                        tones.extend([-1, tone])
                        word2ph.append(2)
                    break
    assert len(initials_finals) == len(tones)

    ###魔改为辅音+带音调的元音
    phones = []
    for a, b in zip(initials_finals, tones):
        if b not in [-1, 0]:  ###防止粤语和普通话重合开头加Y，如果是标点，不加。
            todo = "%s%s" % (a, b)
        else:
            todo = a
        if todo not in punctuation_set:
            todo = "Y%s" % todo
        phones.append(todo)

    # return initials_finals, tones, word2ph
    return phones, word2ph