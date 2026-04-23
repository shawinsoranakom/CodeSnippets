def fit(self, X, y=None):
        """Learn a list of feature name -> indices mappings.

        Parameters
        ----------
        X : Mapping or iterable over Mappings
            Dict(s) or Mapping(s) from feature names (arbitrary Python
            objects) to feature values (strings or convertible to dtype).

            .. versionchanged:: 0.24
               Accepts multiple string values for one categorical feature.

        y : (ignored)
            Ignored parameter.

        Returns
        -------
        self : object
            DictVectorizer class instance.
        """
        feature_names = []
        vocab = {}

        for x in X:
            for f, v in x.items():
                if isinstance(v, str):
                    feature_name = "%s%s%s" % (f, self.separator, v)
                elif isinstance(v, Number) or (v is None):
                    feature_name = f
                elif isinstance(v, Mapping):
                    raise TypeError(
                        f"Unsupported value type {type(v)} "
                        f"for {f}: {v}.\n"
                        "Mapping objects are not supported."
                    )
                elif isinstance(v, Iterable):
                    feature_name = None
                    self._add_iterable_element(f, v, feature_names, vocab)

                if feature_name is not None:
                    if feature_name not in vocab:
                        vocab[feature_name] = len(feature_names)
                        feature_names.append(feature_name)

        if self.sort:
            feature_names.sort()
            vocab = {f: i for i, f in enumerate(feature_names)}

        self.feature_names_ = feature_names
        self.vocabulary_ = vocab

        return self