def predict_proba(self, X):
        """Calculate calibrated probabilities.

        Calculates classification calibrated probabilities
        for each class, in a one-vs-all manner, for `X`.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            The sample data.

        Returns
        -------
        proba : array, shape (n_samples, n_classes)
            The predicted probabilities. Can be exact zeros.
        """
        predictions, _ = _get_response_values(
            self.estimator,
            X,
            response_method=["decision_function", "predict_proba"],
        )
        if predictions.ndim == 1:
            # Reshape binary output from `(n_samples,)` to `(n_samples, 1)`
            predictions = predictions.reshape(-1, 1)

        n_classes = self.classes.shape[0]

        proba = np.zeros((_num_samples(X), n_classes))

        if self.method in ("sigmoid", "isotonic"):
            label_encoder = LabelEncoder().fit(self.classes)
            pos_class_indices = label_encoder.transform(self.estimator.classes_)
            for class_idx, this_pred, calibrator in zip(
                pos_class_indices, predictions.T, self.calibrators
            ):
                if n_classes == 2:
                    # When binary, `predictions` consists only of predictions for
                    # clf.classes_[1] but `pos_class_indices` = 0
                    class_idx += 1
                proba[:, class_idx] = calibrator.predict(this_pred)
            # Normalize the probabilities
            if n_classes == 2:
                proba[:, 0] = 1.0 - proba[:, 1]
            else:
                denominator = np.sum(proba, axis=1)[:, np.newaxis]
                # In the edge case where for each class calibrator returns a zero
                # probability for a given sample, use the uniform distribution
                # instead.
                uniform_proba = np.full_like(proba, 1 / n_classes)
                proba = np.divide(
                    proba, denominator, out=uniform_proba, where=denominator != 0
                )
        elif self.method == "temperature":
            xp, _ = get_namespace(predictions)
            if n_classes == 2 and predictions.shape[-1] == 1:
                response_method_name = _check_response_method(
                    self.estimator,
                    ["decision_function", "predict_proba"],
                ).__name__
                if response_method_name == "predict_proba":
                    predictions = xp.concat([1 - predictions, predictions], axis=1)
            proba = self.calibrators[0].predict(predictions)

        # Deal with cases where the predicted probability minimally exceeds 1.0
        proba[(1.0 < proba) & (proba <= 1.0 + 1e-5)] = 1.0

        return proba