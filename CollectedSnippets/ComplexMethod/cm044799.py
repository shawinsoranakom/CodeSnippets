def _g2p(segments):
    phones_list = []
    word2ph = []
    g2pw_batch_results = []
    g2pw_batch_cursor = 0
    processed_segments = [re.sub("[a-zA-Z]+", "", seg) for seg in segments]
    if is_g2pw:
        batch_inputs = [seg for seg in processed_segments if seg]
        g2pw_batch_results = g2pw._g2pw(batch_inputs) if batch_inputs else []

    for seg in processed_segments:
        pinyins = []
        seg_cut = psg.lcut(seg)
        seg_cut = tone_modifier.pre_merge_for_modify(seg_cut)
        initials = []
        finals = []

        if not is_g2pw:
            for word, pos in seg_cut:
                if pos == "eng":
                    continue
                sub_initials, sub_finals = _get_initials_finals(word)
                sub_finals = tone_modifier.modified_tone(word, pos, sub_finals)
                # 儿化
                sub_initials, sub_finals = _merge_erhua(sub_initials, sub_finals, word, pos)
                initials.append(sub_initials)
                finals.append(sub_finals)
                # assert len(sub_initials) == len(sub_finals) == len(word)
            initials = sum(initials, [])
            finals = sum(finals, [])
            print("pypinyin结果", initials, finals)
        else:
            # g2pw采用整句推理（批量推理，逐句取结果）
            if seg:
                pinyins = g2pw_batch_results[g2pw_batch_cursor]
                g2pw_batch_cursor += 1

            pre_word_length = 0
            for word, pos in seg_cut:
                sub_initials = []
                sub_finals = []
                now_word_length = pre_word_length + len(word)

                if pos == "eng":
                    pre_word_length = now_word_length
                    continue

                word_pinyins = pinyins[pre_word_length:now_word_length]

                # 多音字消歧
                word_pinyins = correct_pronunciation(word, word_pinyins)

                for pinyin in word_pinyins:
                    if pinyin[0].isalpha():
                        sub_initials.append(to_initials(pinyin))
                        sub_finals.append(to_finals_tone3(pinyin, neutral_tone_with_five=True))
                    else:
                        sub_initials.append(pinyin)
                        sub_finals.append(pinyin)

                pre_word_length = now_word_length
                sub_finals = tone_modifier.modified_tone(word, pos, sub_finals)
                # 儿化
                sub_initials, sub_finals = _merge_erhua(sub_initials, sub_finals, word, pos)
                initials.append(sub_initials)
                finals.append(sub_finals)

            initials = sum(initials, [])
            finals = sum(finals, [])
            # print("g2pw结果",initials,finals)

        for c, v in zip(initials, finals):
            raw_pinyin = c + v
            # NOTE: post process for pypinyin outputs
            # we discriminate i, ii and iii
            if c == v:
                assert c in punctuation
                phone = [c]
                word2ph.append(1)
            else:
                v_without_tone = v[:-1]
                tone = v[-1]

                pinyin = c + v_without_tone
                assert tone in "12345"

                if c:
                    # 多音节
                    v_rep_map = {
                        "uei": "ui",
                        "iou": "iu",
                        "uen": "un",
                    }
                    if v_without_tone in v_rep_map.keys():
                        pinyin = c + v_rep_map[v_without_tone]
                else:
                    # 单音节
                    pinyin_rep_map = {
                        "ing": "ying",
                        "i": "yi",
                        "in": "yin",
                        "u": "wu",
                    }
                    if pinyin in pinyin_rep_map.keys():
                        pinyin = pinyin_rep_map[pinyin]
                    else:
                        single_rep_map = {
                            "v": "yu",
                            "e": "e",
                            "i": "y",
                            "u": "w",
                        }
                        if pinyin[0] in single_rep_map.keys():
                            pinyin = single_rep_map[pinyin[0]] + pinyin[1:]

                assert pinyin in pinyin_to_symbol_map.keys(), (pinyin, seg, raw_pinyin)
                new_c, new_v = pinyin_to_symbol_map[pinyin].split(" ")
                new_v = new_v + tone
                phone = [new_c, new_v]
                word2ph.append(len(phone))

            phones_list += phone
    return phones_list, word2ph