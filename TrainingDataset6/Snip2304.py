def get_key():
    ch = getch()

    if ch in const.KEY_MAPPING:
        return const.KEY_MAPPING[ch]
    elif ch == '\x1b':
        next_ch = getch()
        if next_ch == '[':
            last_ch = getch()

            if last_ch == 'A':
                return const.KEY_UP
            elif last_ch == 'B':
                return const.KEY_DOWN

    return ch