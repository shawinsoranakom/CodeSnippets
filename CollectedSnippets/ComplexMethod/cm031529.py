def getwords(self):
        "Return a list of words that match the prefix before the cursor."
        word = self.getprevword()
        if not word:
            return []
        before = self.text.get("1.0", "insert wordstart")
        wbefore = re.findall(r"\b" + word + r"\w+\b", before)
        del before
        after = self.text.get("insert wordend", "end")
        wafter = re.findall(r"\b" + word + r"\w+\b", after)
        del after
        if not wbefore and not wafter:
            return []
        words = []
        dict = {}
        # search backwards through words before
        wbefore.reverse()
        for w in wbefore:
            if dict.get(w):
                continue
            words.append(w)
            dict[w] = w
        # search onwards through words after
        for w in wafter:
            if dict.get(w):
                continue
            words.append(w)
            dict[w] = w
        words.append(word)
        return words