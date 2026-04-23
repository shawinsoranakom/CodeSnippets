def blockType(b):
        patt = [
            ("^(20|19)[0-9]{2}[年/-][0-9]{1,2}[月/-][0-9]{1,2}日*$", "Dt"),
            (r"^(20|19)[0-9]{2}年$", "Dt"),
            (r"^(20|19)[0-9]{2}[年-][0-9]{1,2}月*$", "Dt"),
            ("^[0-9]{1,2}[月-][0-9]{1,2}日*$", "Dt"),
            (r"^第*[一二三四1-4]季度$", "Dt"),
            (r"^(20|19)[0-9]{2}年*[一二三四1-4]季度$", "Dt"),
            (r"^(20|19)[0-9]{2}[ABCDE]$", "Dt"),
            ("^[0-9.,+%/ -]+$", "Nu"),
            (r"^[0-9A-Z/\._~-]+$", "Ca"),
            (r"^[A-Z]*[a-z' -]+$", "En"),
            (r"^[0-9.,+-]+[0-9A-Za-z/$￥%<>（）()' -]+$", "NE"),
            (r"^.{1}$", "Sg"),
        ]
        for p, n in patt:
            if re.search(p, b["text"].strip()):
                return n
        tks = [t for t in rag_tokenizer.tokenize(b["text"]).split() if len(t) > 1]
        if len(tks) > 3:
            if len(tks) < 12:
                return "Tx"
            else:
                return "Lx"

        if len(tks) == 1 and rag_tokenizer.tag(tks[0]) == "nr":
            return "Nr"

        return "Ot"