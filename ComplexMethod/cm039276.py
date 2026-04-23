def fit_transform(self, raw_documents, y=None):
        """Learn the vocabulary dictionary and return document-term matrix.

        This is equivalent to fit followed by transform, but more efficiently
        implemented.

        Parameters
        ----------
        raw_documents : iterable
            An iterable which generates either str, unicode or file objects.

        y : None
            This parameter is ignored.

        Returns
        -------
        X : array of shape (n_samples, n_features)
            Document-term matrix.
        """
        # We intentionally don't call the transform method to make
        # fit_transform overridable without unwanted side effects in
        # TfidfVectorizer.
        if isinstance(raw_documents, str):
            raise ValueError(
                "Iterable over raw text documents expected, string object received."
            )

        self._validate_ngram_range()
        self._warn_for_unused_params()
        self._validate_vocabulary()
        max_df = self.max_df
        min_df = self.min_df
        max_features = self.max_features

        if self.fixed_vocabulary_ and self.lowercase:
            for term in self.vocabulary:
                if any(map(str.isupper, term)):
                    warnings.warn(
                        "Upper case characters found in"
                        " vocabulary while 'lowercase'"
                        " is True. These entries will not"
                        " be matched with any documents"
                    )
                    break

        vocabulary, X = self._count_vocab(raw_documents, self.fixed_vocabulary_)

        if self.binary:
            X.data.fill(1)

        if not self.fixed_vocabulary_:
            n_doc = X.shape[0]
            max_doc_count = max_df if isinstance(max_df, Integral) else max_df * n_doc
            min_doc_count = min_df if isinstance(min_df, Integral) else min_df * n_doc
            if max_doc_count < min_doc_count:
                raise ValueError("max_df corresponds to < documents than min_df")
            if max_features is not None:
                X = self._sort_features(X, vocabulary)
            X = self._limit_features(
                X, vocabulary, max_doc_count, min_doc_count, max_features
            )
            if max_features is None:
                X = self._sort_features(X, vocabulary)
            self.vocabulary_ = vocabulary

        return _align_api_if_sparse(X)