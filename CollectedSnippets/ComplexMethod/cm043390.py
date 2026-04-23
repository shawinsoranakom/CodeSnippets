def preprocess_text(self, text: str) -> List[str]:
        parts = [x.strip() for x in text.split("|")] if "|" in text else [text]
        # Remove : after the first word of parts[0]
        parts[0] = re.sub(r"^(.*?):", r"\1", parts[0])

        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words("english")) - {
            "how",
            "what",
            "when",
            "where",
            "why",
            "which",
        }

        tokens = []
        for part in parts:
            if "(" in part and ")" in part:
                code_tokens = re.findall(
                    r'[\w_]+(?=\()|[\w_]+(?==[\'"]{1}[\w_]+[\'"]{1})', part
                )
                tokens.extend(code_tokens)

            words = word_tokenize(part.lower())
            tokens.extend(
                [
                    lemmatizer.lemmatize(token)
                    for token in words
                    if token not in stop_words
                ]
            )

        return tokens