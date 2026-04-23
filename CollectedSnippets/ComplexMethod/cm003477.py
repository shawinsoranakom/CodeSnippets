def tokenize(self, text, never_split=None, **kwargs):
        """Tokenizes a piece of text."""
        if self.normalize_text:
            text = unicodedata.normalize("NFKC", text)

        text = text.strip()

        never_split = self.never_split + (never_split if never_split is not None else [])
        tokens = []

        for mrph in self.juman.apply_to_sentence(text).morphemes:
            token = mrph.text

            if self.do_lower_case and token not in never_split:
                token = token.lower()

            if self.trim_whitespace:
                if token.strip() == "":
                    continue
                else:
                    token = token.strip()

            tokens.append(token)

        return tokens