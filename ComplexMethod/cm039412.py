def _concatenate_predictions(self, X, predictions):
        """Concatenate the predictions of each first layer learner and
        possibly the input dataset `X`.

        If `X` is sparse and `self.passthrough` is False, the output of
        `transform` will be dense (the predictions). If `X` is sparse
        and `self.passthrough` is True, the output of `transform` will
        be sparse.

        This helper is in charge of ensuring the predictions are 2D arrays and
        it will drop one of the probability column when using probabilities
        in the binary case. Indeed, the p(y|c=0) = 1 - p(y|c=1)

        When `y` type is `"multilabel-indicator"`` and the method used is
        `predict_proba`, `preds` can be either a `ndarray` of shape
        `(n_samples, n_class)` or for some estimators a list of `ndarray`.
        This function will drop one of the probability column in this situation as well.
        """
        X_meta = []
        for est_idx, preds in enumerate(predictions):
            if isinstance(preds, list):
                # `preds` is here a list of `n_targets` 2D ndarrays of
                # `n_classes` columns. The k-th column contains the
                # probabilities of the samples belonging the k-th class.
                #
                # Since those probabilities must sum to one for each sample,
                # we can work with probabilities of `n_classes - 1` classes.
                # Hence we drop the first column.
                for pred in preds:
                    X_meta.append(pred[:, 1:])
            elif preds.ndim == 1:
                # Some estimator return a 1D array for predictions
                # which must be 2-dimensional arrays.
                X_meta.append(preds.reshape(-1, 1))
            elif (
                self.stack_method_[est_idx] == "predict_proba"
                and len(self.classes_) == 2
            ):
                # Remove the first column when using probabilities in
                # binary classification because both features `preds` are perfectly
                # collinear.
                X_meta.append(preds[:, 1:])
            else:
                X_meta.append(preds)

        self._n_feature_outs = [pred.shape[1] for pred in X_meta]
        if self.passthrough:
            X_meta.append(X)
            if sparse.issparse(X):
                return sparse.hstack(X_meta, format=X.format)

        return np.hstack(X_meta)