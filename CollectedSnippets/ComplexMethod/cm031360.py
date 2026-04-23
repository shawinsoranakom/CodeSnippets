def build_menu(
        cons: console.Console,
        wordlist: list[str],
        start: int,
        use_brackets: bool,
        sort_in_column: bool,
) -> tuple[list[str], int]:
    if use_brackets:
        item = "[ %s ]"
        padding = 4
    else:
        item = "%s  "
        padding = 2
    maxlen = min(max(map(real_len, wordlist)), cons.width - padding)
    cols = int(cons.width / (maxlen + padding))
    rows = int((len(wordlist) - 1)/cols + 1)

    if sort_in_column:
        # sort_in_column=False (default)     sort_in_column=True
        #          A B C                       A D G
        #          D E F                       B E
        #          G                           C F
        #
        # "fill" the table with empty words, so we always have the same amount
        # of rows for each column
        missing = cols*rows - len(wordlist)
        wordlist = wordlist + ['']*missing
        indexes = [(i % cols) * rows + i // cols for i in range(len(wordlist))]
        wordlist = [wordlist[i] for i in indexes]
    menu = []
    i = start
    for r in range(rows):
        row = []
        for col in range(cols):
            row.append(item % left_align(wordlist[i], maxlen))
            i += 1
            if i >= len(wordlist):
                break
        menu.append(''.join(row))
        if i >= len(wordlist):
            i = 0
            break
        if r + 5 > cons.height:
            menu.append("   %d more... " % (len(wordlist) - i))
            break
    return menu, i