def weights(self, tks, preprocess=True):
        num_pattern = re.compile(r"[0-9,.]{2,}$")
        short_letter_pattern = re.compile(r"[a-z]{1,2}$")
        num_space_pattern = re.compile(r"[0-9. -]{2,}$")
        letter_pattern = re.compile(r"[a-z. -]+$")

        def ner(t):
            if num_pattern.match(t):
                return 2
            if short_letter_pattern.match(t):
                return 0.01
            if not self.ne or t not in self.ne:
                return 1
            m = {"toxic": 2, "func": 1, "corp": 3, "loca": 3, "sch": 3, "stock": 3,
                 "firstnm": 1}
            return m[self.ne[t]]

        def postag(t):
            t = rag_tokenizer.tag(t)
            if t in set(["r", "c", "d"]):
                return 0.3
            if t in set(["ns", "nt"]):
                return 3
            if t in set(["n"]):
                return 2
            if re.match(r"[0-9-]+", t):
                return 2
            return 1

        def freq(t):
            if num_space_pattern.match(t):
                return 3
            s = rag_tokenizer.freq(t)
            if not s and letter_pattern.match(t):
                return 300
            if not s:
                s = 0

            if not s and len(t) >= 4:
                s = [tt for tt in rag_tokenizer.fine_grained_tokenize(t).split() if len(tt) > 1]
                if len(s) > 1:
                    s = np.min([freq(tt) for tt in s]) / 6.
                else:
                    s = 0

            return max(s, 10)

        def df(t):
            if num_space_pattern.match(t):
                return 5
            if t in self.df:
                return self.df[t] + 3
            elif letter_pattern.match(t):
                return 300
            elif len(t) >= 4:
                s = [tt for tt in rag_tokenizer.fine_grained_tokenize(t).split() if len(tt) > 1]
                if len(s) > 1:
                    return max(3, np.min([df(tt) for tt in s]) / 6.)

            return 3

        def idf(s, N):
            return math.log10(10 + ((N - s + 0.5) / (s + 0.5)))

        tw = []
        if not preprocess:
            idf1 = np.array([idf(freq(t), 10000000) for t in tks])
            idf2 = np.array([idf(df(t), 1000000000) for t in tks])
            wts = (0.3 * idf1 + 0.7 * idf2) * \
                  np.array([ner(t) * postag(t) for t in tks])
            wts = [s for s in wts]
            tw = list(zip(tks, wts))
        else:
            for tk in tks:
                tt = self.token_merge(self.pretoken(tk, True))
                idf1 = np.array([idf(freq(t), 10000000) for t in tt])
                idf2 = np.array([idf(df(t), 1000000000) for t in tt])
                wts = (0.3 * idf1 + 0.7 * idf2) * \
                      np.array([ner(t) * postag(t) for t in tt])
                wts = [s for s in wts]
                tw.extend(zip(tt, wts))

        S = np.sum([s for _, s in tw])
        return [(t, s / S) for t, s in tw]