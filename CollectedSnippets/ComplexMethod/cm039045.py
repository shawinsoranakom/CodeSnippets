def predict(self, X):
        """Perform classification on test vectors X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Test data.

        Returns
        -------
        y : array-like of shape (n_samples,) or (n_samples, n_outputs)
            Predicted target values for X.
        """
        check_is_fitted(self)

        # numpy random_state expects Python int and not long as size argument
        # under Windows
        n_samples = _num_samples(X)
        rs = check_random_state(self.random_state)

        n_classes_ = self.n_classes_
        classes_ = self.classes_
        class_prior_ = self.class_prior_
        constant = self.constant
        if self.n_outputs_ == 1:
            # Get same type even for self.n_outputs_ == 1
            n_classes_ = [n_classes_]
            classes_ = [classes_]
            class_prior_ = [class_prior_]
            constant = [constant]
        # Compute probability only once
        if self._strategy == "stratified":
            proba = self.predict_proba(X)
            if self.n_outputs_ == 1:
                proba = [proba]

        if self.sparse_output_:
            class_prob = None
            if self._strategy in ("most_frequent", "prior"):
                classes_ = [np.array([cp.argmax()]) for cp in class_prior_]

            elif self._strategy == "stratified":
                class_prob = class_prior_

            elif self._strategy == "uniform":
                raise ValueError(
                    "Sparse target prediction is not "
                    "supported with the uniform strategy"
                )

            elif self._strategy == "constant":
                classes_ = [np.array([c]) for c in constant]

            y = _random_choice_csc(n_samples, classes_, class_prob, self.random_state)
        else:
            if self._strategy in ("most_frequent", "prior"):
                y = np.tile(
                    [
                        classes_[k][class_prior_[k].argmax()]
                        for k in range(self.n_outputs_)
                    ],
                    [n_samples, 1],
                )

            elif self._strategy == "stratified":
                y = np.vstack(
                    [
                        classes_[k][proba[k].argmax(axis=1)]
                        for k in range(self.n_outputs_)
                    ]
                ).T

            elif self._strategy == "uniform":
                ret = [
                    classes_[k][rs.randint(n_classes_[k], size=n_samples)]
                    for k in range(self.n_outputs_)
                ]
                y = np.vstack(ret).T

            elif self._strategy == "constant":
                y = np.tile(self.constant, (n_samples, 1))

            if self.n_outputs_ == 1:
                y = np.ravel(y)

        return y