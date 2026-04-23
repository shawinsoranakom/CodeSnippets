def _hstack(self, Xs):
        xp, _ = get_namespace(*Xs)
        # Check if Xs dimensions are valid
        for X, (name, _) in zip(Xs, self.transformer_list):
            if hasattr(X, "shape") and len(X.shape) != 2:
                raise ValueError(
                    f"Transformer '{name}' returned an array or dataframe with "
                    f"{len(X.shape)} dimensions, but expected 2 dimensions "
                    "(n_samples, n_features)."
                )

        adapter = _get_container_adapter("transform", self)
        if adapter and all(adapter.is_supported_container(X) for X in Xs):
            return adapter.hstack(Xs, self.get_feature_names_out())

        if any(sparse.issparse(f) for f in Xs):
            return sparse.hstack(Xs).tocsr()

        return xp.concat(Xs, axis=1)