def highlight(self, txt: str, tks: str, question: str, keywords: list[str]) -> Optional[str]:
        if not txt or not keywords:
            return None

        highlighted_txt = txt

        if question and not self.is_chinese(question):
            highlighted_txt = re.sub(
                r"(^|\W)(%s)(\W|$)" % re.escape(question),
                r"\1<em>\2</em>\3", highlighted_txt,
                flags=re.IGNORECASE | re.MULTILINE,
            )
            if re.search(r"<em>[^<>]+</em>", highlighted_txt, flags=re.IGNORECASE | re.MULTILINE):
                return highlighted_txt

            for keyword in keywords:
                highlighted_txt = re.sub(
                    r"(^|\W)(%s)(\W|$)" % re.escape(keyword),
                    r"\1<em>\2</em>\3", highlighted_txt,
                    flags=re.IGNORECASE | re.MULTILINE,
                )
            if len(re.findall(r'</em><em>', highlighted_txt)) > 0 or len(
                re.findall(r'</em>\s*<em>', highlighted_txt)) > 0:
                return highlighted_txt
            else:
                return None

        if not tks:
            tks = rag_tokenizer.tokenize(txt)
        tokens = tks.split()
        if not tokens:
            return None

        last_pos = len(txt)

        for i in range(len(tokens) - 1, -1, -1):
            token = tokens[i]
            token_pos = highlighted_txt.rfind(token, 0, last_pos)
            if token_pos != -1:
                if token in keywords:
                    highlighted_txt = (
                        highlighted_txt[:token_pos] +
                        f'<em>{token}</em>' +
                        highlighted_txt[token_pos + len(token):]
                    )
                last_pos = token_pos
        return re.sub(r'</em><em>', '', highlighted_txt)