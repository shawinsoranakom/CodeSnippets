def sequences_to_matrix(self, sequences, mode="binary"):
        if not self.num_words:
            if self.word_index:
                num_words = len(self.word_index) + 1
            else:
                raise ValueError(
                    "Specify a dimension (`num_words` argument), "
                    "or fit on some text data first."
                )
        else:
            num_words = self.num_words

        if mode == "tfidf" and not self.document_count:
            raise ValueError(
                "Fit the Tokenizer on some data before using tfidf mode."
            )

        x = np.zeros((len(sequences), num_words))
        for i, seq in enumerate(sequences):
            if not seq:
                continue
            counts = collections.defaultdict(int)
            for j in seq:
                if j >= num_words:
                    continue
                counts[j] += 1
            for j, c in list(counts.items()):
                if mode == "count":
                    x[i][j] = c
                elif mode == "freq":
                    x[i][j] = c / len(seq)
                elif mode == "binary":
                    x[i][j] = 1
                elif mode == "tfidf":
                    # Use weighting scheme 2 in
                    # https://en.wikipedia.org/wiki/Tf%E2%80%93idf
                    tf = 1 + np.log(c)
                    idf = np.log(
                        1
                        + self.document_count / (1 + self.index_docs.get(j, 0))
                    )
                    x[i][j] = tf * idf
                else:
                    raise ValueError("Unknown vectorization mode:", mode)
        return x