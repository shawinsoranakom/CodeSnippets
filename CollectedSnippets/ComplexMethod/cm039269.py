def _transform(self, X, fitting):
        # Sanity check: Python's array has no way of explicitly requesting the
        # signed 32-bit integers that scipy.sparse needs, so we use the next
        # best thing: typecode "i" (int). However, if that gives larger or
        # smaller integers than 32-bit ones, np.frombuffer screws up.
        assert array("i").itemsize == 4, (
            "sizeof(int) != 4 on your platform; please report this at"
            " https://github.com/scikit-learn/scikit-learn/issues and"
            " include the output from platform.platform() in your bug report"
        )

        dtype = self.dtype
        if fitting:
            feature_names = []
            vocab = {}
        else:
            feature_names = self.feature_names_
            vocab = self.vocabulary_

        transforming = True

        # Process everything as sparse regardless of setting
        X = [X] if isinstance(X, Mapping) else X

        indices = array("i")
        indptr = [0]
        # XXX we could change values to an array.array as well, but it
        # would require (heuristic) conversion of dtype to typecode...
        values = []

        # collect all the possible feature names and build sparse matrix at
        # same time
        for x in X:
            for f, v in x.items():
                if isinstance(v, str):
                    feature_name = "%s%s%s" % (f, self.separator, v)
                    v = 1
                elif isinstance(v, Number) or (v is None):
                    feature_name = f
                elif not isinstance(v, Mapping) and isinstance(v, Iterable):
                    feature_name = None
                    self._add_iterable_element(
                        f,
                        v,
                        feature_names,
                        vocab,
                        fitting=fitting,
                        transforming=transforming,
                        indices=indices,
                        values=values,
                    )
                else:
                    raise TypeError(
                        f"Unsupported value Type {type(v)} "
                        f"for {f}: {v}.\n"
                        f"{type(v)} objects are not supported."
                    )

                if feature_name is not None:
                    if fitting and feature_name not in vocab:
                        vocab[feature_name] = len(feature_names)
                        feature_names.append(feature_name)

                    if feature_name in vocab:
                        indices.append(vocab[feature_name])
                        values.append(self.dtype(v))

            indptr.append(len(indices))

        if len(indptr) == 1:
            raise ValueError("Sample sequence X is empty.")

        indices = np.frombuffer(indices, dtype=np.intc)
        shape = (len(indptr) - 1, len(vocab))

        result_matrix = sp.csr_array(
            (values, indices, indptr), shape=shape, dtype=dtype
        )

        # Sort everything if asked
        if fitting and self.sort:
            feature_names.sort()
            map_index = np.empty(len(feature_names), dtype=np.int32)
            for new_val, f in enumerate(feature_names):
                map_index[new_val] = vocab[f]
                vocab[f] = new_val
            result_matrix = result_matrix[:, map_index]

        if self.sparse:
            result_matrix.sort_indices()
        else:
            result_matrix = result_matrix.toarray()

        if fitting:
            self.feature_names_ = feature_names
            self.vocabulary_ = vocab

        return _align_api_if_sparse(result_matrix)