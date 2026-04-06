def _decompose_korean(command):
    def _change_double(ch):
        if ch in DOUBLE_LIST:
            return DOUBLE_MOD_LIST[DOUBLE_LIST.index(ch)]
        return ch

    hg_str = u''
    for ch in command.script:
        if u'가' <= ch <= u'힣':
            ord_ch = ord(ch) - ord(u'가')
            hd = ord_ch // 588
            bd = (ord_ch - 588 * hd) // 28
            tl = ord_ch - 588 * hd - 28 * bd
            for ch in [HEAD_LIST[hd], BODY_LIST[bd], TAIL_LIST[tl]]:
                if ch != ' ':
                    hg_str += _change_double(ch)
        else:
            hg_str += _change_double(ch)
    return hg_str