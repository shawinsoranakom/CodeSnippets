def question(self, txt, tbl="qa", min_match: float = 0.6):
        original_query = txt
        txt = self.add_space_between_eng_zh(txt)

        # Strip Infinity ESCAPABLE characters from the query.
        #
        # Infinity's search_lexer.l defines ESCAPABLE characters [\x20()^"'~*?:\\]
        # If these characters appear unescaped in a query, Infinity's lexer will
        # interpret them as special tokens, causing parsing errors.
        txt = re.sub(
            r"[ :|\r\n\t,，。？?/`!！&^%%()\[\]{}<>*~'\"\\]+",
            " ",
            rag_tokenizer.tradi2simp(rag_tokenizer.strQ2B(txt.lower())),
        ).strip()
        otxt = txt
        txt = self.rmWWW(txt)

        if not self.is_chinese(txt):
            txt = self.rmWWW(txt)
            tks = rag_tokenizer.tokenize(txt).split()
            keywords = [t for t in tks if t]
            tks_w = self.tw.weights(tks, preprocess=False)
            tks_w = [(re.sub(r"[ \\\"'^]", "", tk), w) for tk, w in tks_w]
            tks_w = [(re.sub(r"^[\+-]", "", tk), w) for tk, w in tks_w if tk]
            tks_w = [(tk.strip(), w) for tk, w in tks_w if tk.strip()]
            syns = []
            for tk, w in tks_w[:256]:
                # Strip single quotes from synonym terms to avoid Infinity lexer TokenError
                # (e.g. WordNet returns "cat-o'-nine-tails" for "cat")
                syn = [rag_tokenizer.tokenize(s).replace("'", "") for s in self.syn.lookup(tk)]
                keywords.extend(syn)
                syn = ["\"{}\"^{:.4f}".format(s, w / 4.) for s in syn if s.strip()]
                syns.append(" ".join(syn))

            q = ["({}^{:.4f}".format(tk, w) + " {})".format(syn) for (tk, w), syn in zip(tks_w, syns) if
                 tk and not re.match(r"[.^+\(\)-]", tk)]
            for i in range(1, len(tks_w)):
                left, right = tks_w[i - 1][0].strip(), tks_w[i][0].strip()
                if not left or not right:
                    continue
                q.append(
                    '"%s %s"^%.4f'
                    % (
                        tks_w[i - 1][0],
                        tks_w[i][0],
                        max(tks_w[i - 1][1], tks_w[i][1]) * 2,
                    )
                )
            if not q:
                q.append(txt)
            query = " ".join(q)
            return MatchTextExpr(
                self.query_fields, query, 100, {"original_query": original_query}
            ), keywords

        def need_fine_grained_tokenize(tk):
            if len(tk) < 3:
                return False
            if re.match(r"[0-9a-z\.\+#_\*-]+$", tk):
                return False
            return True

        txt = self.rmWWW(txt)
        qs, keywords = [], []
        for tt in self.tw.split(txt)[:256]:  # .split():
            if not tt:
                continue
            keywords.append(tt)
            twts = self.tw.weights([tt])
            syns = self.syn.lookup(tt)
            if syns and len(keywords) < 32:
                keywords.extend(syns)
            logging.debug(json.dumps(twts, ensure_ascii=False))
            tms = []
            for tk, w in sorted(twts, key=lambda x: x[1] * -1):
                sm = (
                    rag_tokenizer.fine_grained_tokenize(tk).split()
                    if need_fine_grained_tokenize(tk)
                    else []
                )
                sm = [
                    re.sub(
                        r"[ ,\./;'\[\]\\`~!@#$%\^&\*\(\)=\+_<>\?:\"\{\}\|，。；‘’【】、！￥……（）——《》？：“”-]+",
                        "",
                        m,
                    )
                    for m in sm
                ]
                sm = [self.sub_special_char(m) for m in sm if len(m) > 1]
                sm = [m for m in sm if len(m) > 1]

                if len(keywords) < 32:
                    keywords.append(re.sub(r"[ \\\"']+", "", tk))
                    keywords.extend(sm)

                tk_syns = self.syn.lookup(tk)
                tk_syns = [self.sub_special_char(s) for s in tk_syns]
                if len(keywords) < 32:
                    keywords.extend([s for s in tk_syns if s])
                tk_syns = [rag_tokenizer.fine_grained_tokenize(s) for s in tk_syns if s]
                tk_syns = [f"\"{s}\"" if s.find(" ") > 0 else s for s in tk_syns]

                if len(keywords) >= 32:
                    break

                tk = self.sub_special_char(tk)
                if tk.find(" ") > 0:
                    tk = '"%s"' % tk
                if tk_syns:
                    tk = f"({tk} OR (%s)^0.2)" % " ".join(tk_syns)
                if sm:
                    tk = f'{tk} OR "%s" OR ("%s"~2)^0.5' % (" ".join(sm), " ".join(sm))
                if tk.strip():
                    tms.append((tk, w))

            tms = " ".join([f"({t})^{w}" for t, w in tms])

            if len(twts) > 1:
                tms += ' ("%s"~2)^1.5' % rag_tokenizer.tokenize(tt)

            syns = " OR ".join(
                [
                    '"%s"'
                    % rag_tokenizer.tokenize(self.sub_special_char(s))
                    for s in syns
                ]
            )
            if syns and tms:
                tms = f"({tms})^5 OR ({syns})^0.7"

            qs.append(tms)

        if qs:
            query = " OR ".join([f"({t})" for t in qs if t])
            if not query:
                query = otxt
            return MatchTextExpr(
                self.query_fields, query, 100, {"minimum_should_match": min_match, "original_query": original_query}
            ), keywords
        return None, keywords