def tokenize(self, text, clean=False):
        text = text.replace(" ", "<SP>")
        text = text.replace("　", "<SP>")
        text = text.replace("\r\n", "<BR>")
        text = text.replace("\n", "<BR>")
        text = text.replace("\r", "<BR>")
        text = text.replace("\t", "<TAB>")
        text = text.replace("—", "ー")
        text = text.replace("−", "ー")
        for k, v in self.emoji["emoji"].items():
            if k in text:
                text = text.replace(k, v)
        if clean:
            text = self.clean_text(text)

        def check_simbol(x):
            e = x.encode()
            if len(x) == 1 and len(e) == 2:
                c = (int(e[0]) << 8) + int(e[1])
                if (
                    (c >= 0xC2A1 and c <= 0xC2BF)
                    or (c >= 0xC780 and c <= 0xC783)
                    or (c >= 0xCAB9 and c <= 0xCBBF)
                    or (c >= 0xCC80 and c <= 0xCDA2)
                ):
                    return True
            return False

        def checku2e(x):
            e = x.encode()
            if len(x) == 1 and len(e) == 3:
                c = (int(e[0]) << 16) + (int(e[1]) << 8) + int(e[2])
                if c >= 0xE28080 and c <= 0xE2B07F:
                    return True
            return False

        pos = 0
        result = []
        while pos < len(text):
            end = min(len(text), pos + self.maxlen + 1) if text[pos] == "<" else pos + 3
            candidates = []  # (token_id, token, pos)
            for e in range(end, pos, -1):
                wd = text[pos:e]
                if wd in self.vocab:
                    if wd[0] == "<" and len(wd) > 2:
                        candidates = [(self.vocab[wd], wd, e)]
                        break
                    else:
                        candidates.append((self.vocab[wd], wd, e))
            if len(candidates) > 0:
                # the smallest token_id is adopted
                _, wd, e = min(candidates, key=lambda x: x[0])
                result.append(wd)
                pos = e
            else:
                end = pos + 1
                wd = text[pos:end]
                if check_simbol(wd):
                    result.append("<KIGOU>")
                elif checku2e(wd):
                    result.append("<U2000U2BFF>")
                else:
                    for i in wd.encode("utf-8"):
                        result.append("<|byte%d|>" % i)
                pos = end
        return result